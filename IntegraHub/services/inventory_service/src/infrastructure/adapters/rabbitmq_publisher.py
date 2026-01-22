"""Adaptador publicador RabbitMQ para Inventory Service"""

import json
import logging
from typing import Dict, Any, Optional

import pika

from ...domain.ports import EventPublisher

logger = logging.getLogger(__name__)


class RabbitMQPublisher(EventPublisher):
    """Implementación del publicador de eventos usando RabbitMQ"""

    def __init__(self, host: str, channel: Optional[pika.channel.Channel] = None):
        """
        Inicializa el publicador.

        Args:
            host: Host de RabbitMQ (ignorado si se proporciona channel)
            channel: Canal de RabbitMQ existente para reutilizar
        """
        self._channel = channel
        self._exchange = "integrahub_exchange"

    def publish(self, topic: str, event_type: str, data: Dict[str, Any]) -> None:
        """
        Publica un evento en el exchange de RabbitMQ.

        Args:
            topic: Tópico del evento (usado en routing key)
            event_type: Tipo de evento
            data: Datos del evento
        """
        if not self._channel:
            logger.warning("No hay canal disponible para publicar")
            return

        routing_key = f"{topic}.{event_type}"
        message = {"event_type": event_type, "data": data}

        self._channel.basic_publish(
            exchange=self._exchange,
            routing_key=routing_key,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2, content_type="application/json"  # Mensaje persistente
            ),
        )
        logger.info(f"Evento publicado: {routing_key}")
