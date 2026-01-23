# Infrastructure Adapter: RabbitMQ Publisher
# Implementa el Port EventPublisher usando shared.infrastructure.messaging.
# Esto permite que la lógica de publicación sea reutilizable entre servicios.
 
import os
from ...domain.ports import EventPublisher
from shared.infrastructure.messaging import RabbitMQConnection, BasePublisher

class RabbitMQPublisherAdapter(EventPublisher):
    def __init__(self, host: str = "rabbitmq"):
        # Crea conexión y publisher base con exchange/topic estándar del proyecto.
        self.connection = RabbitMQConnection(host=host)
        self.publisher = BasePublisher(self.connection)
    #pylint: disable=arguments-differ
    def publish(self, topic: str, event_type: str, data: dict):
        # Publica evento de integración con routing_key {topic}.{event_type}
        # Ej: orders.OrderCreated
        self.publisher.publish(topic, event_type, data)

