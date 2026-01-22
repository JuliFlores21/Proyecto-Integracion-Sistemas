import json
import logging
import threading
import pika
from typing import Callable
from ...application.services import UpdateOrderStatusUseCase

logger = logging.getLogger(__name__)


class RabbitMQConsumer:
    def __init__(
        self,
        rabbitmq_host: str,
        rabbitmq_user: str,
        rabbitmq_pass: str,
        update_order_use_case: UpdateOrderStatusUseCase,
    ):
        self.rabbitmq_host = rabbitmq_host
        self.rabbitmq_user = rabbitmq_user
        self.rabbitmq_pass = rabbitmq_pass
        self.update_order_use_case = update_order_use_case
        self.connection = None
        self.channel = None
        self._stop_event = threading.Event()

    def start(self):
        """Inicia el consumidor en un hilo separado"""
        thread = threading.Thread(target=self._run)
        thread.daemon = True
        thread.start()

    def _run(self):
        try:
            credentials = pika.PlainCredentials(self.rabbitmq_user, self.rabbitmq_pass)
            parameters = pika.ConnectionParameters(
                host=self.rabbitmq_host, credentials=credentials
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            # Usar el exchange principal del sistema
            exchange_name = "integrahub_exchange"
            self.channel.exchange_declare(
                exchange=exchange_name, exchange_type="topic", durable=True
            )

            # Declarar cola exclusiva para order-service update
            queue_name = "order_updates_queue"
            self.channel.queue_declare(queue=queue_name, durable=True)

            # Bind a OrderConfirmed (Topic: payments.OrderConfirmed)
            routing_key_confirmed = "payments.OrderConfirmed"
            self.channel.queue_bind(
                exchange=exchange_name,
                queue=queue_name,
                routing_key=routing_key_confirmed,
            )

            # Bind a OrderRejected (Topic: payments.OrderRejected)
            routing_key_rejected = "payments.OrderRejected"
            self.channel.queue_bind(
                exchange=exchange_name,
                queue=queue_name,
                routing_key=routing_key_rejected,
            )

            # Configurar QoS
            self.channel.basic_qos(prefetch_count=1)

            # Configurar consumo
            self.channel.basic_consume(
                queue=queue_name, on_message_callback=self._callback
            )

            logger.info(
                f"Escuchando eventos en {queue_name} vinculada a payments.* ..."
            )
            self.channel.start_consuming()

        except Exception as e:
            logger.error(f"Error en RabbitMQ Consumer: {e}")
            if self.connection and not self.connection.is_closed:
                self.connection.close()

    def _callback(self, ch, method, properties, body):
        try:
            logger.info(f"Evento recibido: {method.routing_key}")
            # El mensaje viene envuelto en un sobre estándar (ver messaging.py)
            envelope = json.loads(body)
            payload = envelope.get("data", {})

            event_type = method.routing_key

            if "OrderConfirmed" in event_type:
                order_id = payload.get("order_id")
                status = payload.get("status", "CONFIRMED")
                if order_id:
                    logger.info(f"Actualizando orden {order_id} a estado {status}")
                    self.update_order_use_case.execute(order_id, "CONFIRMED")

            elif "OrderRejected" in event_type:
                order_id = payload.get("order_id")
                reason = payload.get("reason", "Unknown")
                if order_id:
                    logger.info(f"Rechazando orden {order_id}: {reason}")
                    self.update_order_use_case.execute(order_id, "REJECTED")

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
            # En caso de error, podríamos hacer nack, pero por ahora logueamos
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
