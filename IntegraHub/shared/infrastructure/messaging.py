"""
messaging.py

Infraestructura de mensajería (RabbitMQ) compartida por los microservicios.

- Exchange principal: topic (integrahub_exchange)
- DLQ pattern: DLX (direct) + DLQ por servicio
- Consumidor base: ACK si el handler termina OK, NACK(requeue=False) si falla
  -> RabbitMQ enviará el mensaje al DLQ usando la configuración x-dead-letter-*

NOTA: El publisher tiene retry de conexión (tenacity). El consumer actualmente no reintenta
el procesamiento; el "retry" se logra enviando a DLQ y revisando el mensaje fallido.
"""

import pika
import json
import uuid
import time
from typing import Callable, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class RabbitMQConnection:
    def __init__(self, host: str, user: str = "user", password: str = "password"):
        self.host = host
        self.credentials = pika.PlainCredentials(user, password)
        self.parameters = pika.ConnectionParameters(host=self.host, credentials=self.credentials)
        self.connection = None
        self.channel = None

    def connect(self):
        if not self.connection or self.connection.is_closed:
            # Conexión "lazy": se crea solo si no existe o está cerrada.
            # Importante para contenedores: RabbitMQ puede tardar en estar "healthy".

            print(f" [RabbitMQ] Connecting to {self.host}...")
            self.connection = pika.BlockingConnection(self.parameters)
            self.channel = self.connection.channel()
            # Restore topology defaults if needed here
            # self.setup_topology()

    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()

    def get_channel(self):
        self.connect()
        return self.channel

class BasePublisher:
    def __init__(self, connection: RabbitMQConnection, exchange_name: str = "integrahub_exchange"):
        self.connection_wrapper = connection
        self.exchange_name = exchange_name

    @retry(
        # Retry SOLO para errores de conexión AMQP (no reintenta lógica de negocio).
        # Estrategia: exponential backoff (2s..10s) hasta 5 intentos.

        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(pika.exceptions.AMQPConnectionError)
    )
    def publish(self, topic: str, event_type: str, data: dict, correlation_id: str = None):
        channel = self.connection_wrapper.get_channel()
        channel.exchange_declare(exchange=self.exchange_name, exchange_type='topic', durable=True)

        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Estructura estándar del evento publicado:
        # - event_id: id único del mensaje/evento
        # - event_type: tipo de evento (OrderCreated, OrderConfirmed, etc.)
        # - timestamp: aquí se usa uuid1 como "timestamp simple" (mejorable a datetime ISO)
        # - data: payload del dominio
        # - correlation_id: trazabilidad end-to-end

        message_body = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "timestamp": str(uuid.uuid1()), # simple timestamp
            "data": data,
            "correlation_id": correlation_id
        }

        # Convención de routing key:
        #   {topic}.{event_type}
        # Ej: "order.OrderCreated"
        
        routing_key = f"{topic}.{event_type}"

        channel.basic_publish(
            exchange=self.exchange_name,
            routing_key=routing_key,
            body=json.dumps(message_body),
            
            # delivery_mode=2 => mensaje persistente (si la cola/exchange son durables)
            # correlation_id => se imprime en logs del consumidor para trazabilidad

            properties=pika.BasicProperties(
                delivery_mode=2,
                correlation_id=correlation_id,
                content_type='application/json'
            )
        )
        print(f" [x] Sent {routing_key} (CorrId: {correlation_id})")

class BaseConsumer:
    """
    Base Consumer with DLQ support and automatic binding.
    """
    def __init__(self, connection: RabbitMQConnection, service_name: str, exchange_name: str = "integrahub_exchange"):
        self.connection_wrapper = connection
        self.service_name = service_name
        self.exchange_name = exchange_name
        
        self.dlx_name = "integrahub_dlx"
        self.dlq_name = f"{service_name}_dlq"
        self.queue_name = f"{service_name}_queue"

    def setup_topology(self):
        channel = self.connection_wrapper.get_channel()

        # Topología mínima por servicio:
        # - Exchange topic principal (publicación)
        # - DLX (direct) + DLQ (cola) para mensajes fallidos
        # - Cola principal con x-dead-letter-* apuntando al DLX

        # 1. Main Exchange
        channel.exchange_declare(exchange=self.exchange_name, exchange_type='topic', durable=True)

        # 2. DLX setup
        channel.exchange_declare(exchange=self.dlx_name, exchange_type='direct', durable=True)
        channel.queue_declare(queue=self.dlq_name, durable=True)
        channel.queue_bind(queue=self.dlq_name, exchange=self.dlx_name, routing_key=f"{self.service_name}_dlq_key")

        # Configuración DLQ:
        # Si el consumidor hace NACK(requeue=False), RabbitMQ "dead-letter" el mensaje:
        #   -> lo re-publica al DLX usando la routing key configurada

        # 3. Queue with DLQ config
        args = {
            'x-dead-letter-exchange': self.dlx_name,
            'x-dead-letter-routing-key': f"{self.service_name}_dlq_key"
        }
        channel.queue_declare(queue=self.queue_name, durable=True, arguments=args)
        
        # prefetch_count=1 => procesa 1 mensaje a la vez por consumidor (evita sobrecarga)
        channel.basic_qos(prefetch_count=1)

    def bind_event(self, routing_key: str):
        channel = self.connection_wrapper.get_channel()
        channel.queue_bind(exchange=self.exchange_name, queue=self.queue_name, routing_key=routing_key)

    def start_consuming(self, callback_function: Callable):
        self.setup_topology()
        channel = self.connection_wrapper.get_channel()

        def wrapper_callback(ch, method, properties, body):
            print(f" [x] Received {method.routing_key} | CorrId: {properties.correlation_id}")

            # callback_function debe lanzar excepción si quiere marcar el mensaje como fallido.
            # Éxito => ACK
            # Error => NACK(requeue=False) => DLQ

            try:
                # Pass correlation_id in context if needed, currently just logging
                callback_function(json.loads(body), properties.correlation_id)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                print(f" [!] Error processing: {e}")
                
                # requeue=False:
                # - NO reencola el mensaje en la cola principal (evita loops infinitos)
                # - al existir x-dead-letter-exchange/routing-key, termina en DLQ
                #
                # FUTURO (sin implementar hoy):
                # Para retries/backoff se puede usar:
                # - x-death headers (conteo de dead-letters)
                # - cola de delay con TTL + DLX (reintento diferido)

                
                # Reject -> DLQ
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        print(f" [*] Waiting for messages in {self.queue_name}")
        channel.basic_consume(queue=self.queue_name, on_message_callback=wrapper_callback)
        channel.start_consuming()
