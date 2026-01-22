import pika
import json
from ...application.services import NotificationUseCase

EXCHANGE_NAME = "integrahub_exchange"
QUEUE_NAME = "notification_queue"

class RabbitMQConsumer:
    def __init__(self, amqp_url: str, use_case: NotificationUseCase):
        self.amqp_url = amqp_url
        self.use_case = use_case
        self.connection = None
        self.channel = None

    def connect(self):
        params = pika.URLParameters(self.amqp_url)
        self.connection = pika.BlockingConnection(params)
        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic', durable=True)
        self.channel.queue_declare(queue=QUEUE_NAME, durable=True)

        # Retrieve all relevant events for Notifications
        # Binding keys: *.<Event> allows catching from any service (Source independent)
        binding_keys = [
            "*.OrderCreated",
            "*.OrderConfirmed",
            "*.OrderRejected"
        ]
        
        for key in binding_keys:
            self.channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME, routing_key=key)
            
        print(f" [*] Bound to keys: {binding_keys}")

    def start_consuming(self):
        self.connect()

        def callback(ch, method, properties, body):
            try:
                payload = json.loads(body)
                event_type = payload.get("event_type")
                data = payload.get("data")
                
                print(f" [x] Notification Service received: {event_type}")
                
                self.use_case.execute(event_type, data)
                
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                print(f" [!] Error processing notification: {e}")
                # We ack to avoid loop on bad message for notifications (fire and forget mostly)
                ch.basic_ack(delivery_tag=method.delivery_tag)

        self.channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
        print(' [*] Waiting for notification events...')
        self.channel.start_consuming()
