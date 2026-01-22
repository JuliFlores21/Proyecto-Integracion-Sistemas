import os
from ...domain.ports import EventPublisher
from shared.infrastructure.messaging import RabbitMQConnection, BasePublisher

class RabbitMQPublisherAdapter(EventPublisher):
    def __init__(self, host: str = "rabbitmq"):
        self.connection = RabbitMQConnection(host=host)
        self.publisher = BasePublisher(self.connection)
    #pylint: disable=arguments-differ
    def publish(self, topic: str, event_type: str, data: dict):
        self.publisher.publish(topic, event_type, data)

