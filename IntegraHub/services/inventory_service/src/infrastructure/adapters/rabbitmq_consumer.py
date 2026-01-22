"""Adaptador consumidor RabbitMQ para Inventory Service"""

import json
import logging
import time

import pika
from tenacity import retry, stop_after_attempt, wait_fixed, RetryError

from ...application.services import ReserveInventoryUseCase
from ...domain.ports import InventoryRepository, EventPublisher
from .rabbitmq_publisher import RabbitMQPublisher

logger = logging.getLogger(__name__)

# Constantes de configuración
DLX_NAME = "integrahub_dlx"
DLQ_NAME = "inventory_dlq"
MAIN_EXCHANGE = "integrahub_exchange"
MAIN_QUEUE = "inventory_queue"
MAX_RETRIES = 3


class RabbitMQConsumer:
    """Consumidor de mensajes RabbitMQ para el servicio de inventario"""

    def __init__(self, amqp_url: str, repository: InventoryRepository):
        self._amqp_url = amqp_url
        self._repository = repository
        self._connection = None
        self._channel = None

    def _connect_with_retry(self) -> None:
        """Conecta a RabbitMQ con reintentos"""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                params = pika.URLParameters(self._amqp_url)
                self._connection = pika.BlockingConnection(params)
                self._channel = self._connection.channel()
                logger.info("Conectado a RabbitMQ exitosamente")
                return
            except pika.exceptions.AMQPConnectionError as e:
                logger.warning(f"Intento {attempt + 1}/{max_retries} fallido: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                else:
                    raise

    def _setup_topology(self) -> None:
        """Configura la topología de RabbitMQ (exchanges, queues, bindings)"""
        # 1. Declarar DLX y DLQ
        self._channel.exchange_declare(
            exchange=DLX_NAME, exchange_type="direct", durable=True
        )
        self._channel.queue_declare(queue=DLQ_NAME, durable=True)
        self._channel.queue_bind(
            queue=DLQ_NAME, exchange=DLX_NAME, routing_key="inventory_dlq_key"
        )

        # 2. Declarar Exchange principal y Queue con configuración DLX
        self._channel.exchange_declare(
            exchange=MAIN_EXCHANGE, exchange_type="topic", durable=True
        )

        args = {
            "x-dead-letter-exchange": DLX_NAME,
            "x-dead-letter-routing-key": "inventory_dlq_key",
        }
        self._channel.queue_declare(queue=MAIN_QUEUE, durable=True, arguments=args)

        # 3. Binding para eventos de OrderCreated
        self._channel.queue_bind(
            exchange=MAIN_EXCHANGE, queue=MAIN_QUEUE, routing_key="orders.OrderCreated"
        )

        # Configurar QoS
        self._channel.basic_qos(prefetch_count=1)
        logger.info("Topología de RabbitMQ configurada")

    def start_consuming(self) -> None:
        """Inicia el consumo de mensajes"""
        self._connect_with_retry()
        self._setup_topology()

        # Inicializar publisher compartiendo el canal
        publisher = RabbitMQPublisher(host="ignored", channel=self._channel)
        use_case = ReserveInventoryUseCase(self._repository, publisher)

        logger.info(f"Esperando mensajes en {MAIN_QUEUE}...")

        def callback(ch, method, properties, body):
            logger.info(f"Mensaje recibido: {body[:100]}...")
            try:
                self._process_message_with_retries(use_case, body)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.debug("Mensaje procesado exitosamente")
            except Exception as e:
                logger.error(f"Error al procesar mensaje después de reintentos: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        self._channel.basic_consume(queue=MAIN_QUEUE, on_message_callback=callback)
        self._channel.start_consuming()

    @retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_fixed(1), reraise=True)
    def _process_message_with_retries(
        self, use_case: ReserveInventoryUseCase, body: bytes
    ) -> None:
        """Procesa un mensaje con reintentos automáticos"""
        data = json.loads(body)
        event_data = data.get("data", {})

        order_id = event_data.get("order_id")
        items = event_data.get("items", [])

        if not order_id or not items:
            logger.warning(f"Mensaje con datos incompletos: {data}")
            return

        use_case.execute(order_id, items)
