"""Adaptador consumidor RabbitMQ para Notification Service"""

import json
import logging
import time

import pika

from ...application.services import NotificationUseCase

logger = logging.getLogger(__name__)

# Constantes de configuración
EXCHANGE_NAME = "integrahub_exchange"
QUEUE_NAME = "notification_queue"


class RabbitMQConsumer:
    """Consumidor de mensajes RabbitMQ para notificaciones"""

    def __init__(self, amqp_url: str, use_case: NotificationUseCase):
        self._amqp_url = amqp_url
        self._use_case = use_case
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
        """Configura la topología de RabbitMQ"""
        self._channel.exchange_declare(
            exchange=EXCHANGE_NAME, exchange_type="topic", durable=True
        )
        self._channel.queue_declare(queue=QUEUE_NAME, durable=True)

        # Suscribirse a todos los eventos relevantes para notificaciones
        binding_keys = ["*.OrderCreated", "*.OrderConfirmed", "*.OrderRejected"]

        for key in binding_keys:
            self._channel.queue_bind(
                exchange=EXCHANGE_NAME, queue=QUEUE_NAME, routing_key=key
            )

        logger.info(f"Suscrito a eventos: {binding_keys}")

    def start_consuming(self) -> None:
        """Inicia el consumo de mensajes"""
        self._connect_with_retry()
        self._setup_topology()

        def callback(ch, method, properties, body):
            try:
                payload = json.loads(body)
                event_type = payload.get("event_type")
                data = payload.get("data", {})

                logger.info(f"Evento recibido: {event_type}")
                self._use_case.execute(event_type, data)

                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Error procesando notificación: {e}")
                # ACK para evitar bucle infinito en notificaciones (fire and forget)
                ch.basic_ack(delivery_tag=method.delivery_tag)

        self._channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
        logger.info(f"Esperando eventos de notificación...")
        self._channel.start_consuming()
