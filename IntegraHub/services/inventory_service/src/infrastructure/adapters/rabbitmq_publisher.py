import json
import pika
import os
from ...domain.ports import EventPublisher

class RabbitMQPublisher(EventPublisher):
    def __init__(self, host: str, channel):
        # We share the channel from the consumer if possible, or create new.
        # For simplicity and thread safety, let's assume we might reuse or create.
        # Here we accept an existing channel to Publish on the same connection.
        self.channel = channel
        self.exchange = 'integrahub_exchange'

    def publish(self, topic: str, event_type: str, data: dict):
        routing_key = f"{topic}.{event_type}"
        message = {
            "event_type": event_type,
            "data": data
        }
        
        self.channel.basic_publish(
            exchange=self.exchange,
            routing_key=routing_key,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,
            )
        )
