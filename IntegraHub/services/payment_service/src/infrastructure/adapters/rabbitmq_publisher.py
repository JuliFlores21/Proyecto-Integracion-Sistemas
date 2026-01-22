import json
import pika
import os
from ...domain.ports import EventPublisher

class RabbitMQPublisher(EventPublisher):
    def __init__(self, channel=None):
        self.channel = channel
        self.exchange = 'integrahub_exchange'
        # If channel not provided, we might need to create one, 
        # but usually we share from consumer in this simple setup.

    def publish(self, topic: str, event_type: str, data: dict):
        if not self.channel:
            print("Constructor Warning: No channel provided for publisher")
            return

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
