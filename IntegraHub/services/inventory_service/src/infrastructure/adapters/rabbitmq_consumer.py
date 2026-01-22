import pika
import json
import os
import time
from tenacity import retry, stop_after_attempt, wait_fixed
from ...application.services import ReserveInventoryUseCase
from ...domain.ports import InventoryRepository, EventPublisher
from .rabbitmq_publisher import RabbitMQPublisher

DLX_NAME = "integrahub_dlx"
DLQ_NAME = "inventory_dlq"
MAIN_EXCHANGE = "integrahub_exchange"
MAIN_QUEUE = "inventory_queue"

class RabbitMQConsumer:
    def __init__(self, amqp_url: str, repository: InventoryRepository):
        self.amqp_url = amqp_url
        self.repository = repository
        self.connection = None
        self.channel = None

    def connect(self):
        # Connection with retry handled by main loop or orchestator, 
        # but here we establish the channel and topology.
        params = pika.URLParameters(self.amqp_url)
        self.connection = pika.BlockingConnection(params)
        self.channel = self.connection.channel()

        # 1. Declare DLX and DLQ
        self.channel.exchange_declare(exchange=DLX_NAME, exchange_type='direct', durable=True)
        self.channel.queue_declare(queue=DLQ_NAME, durable=True)
        self.channel.queue_bind(queue=DLQ_NAME, exchange=DLX_NAME, routing_key="inventory_dlq_key")

        # 2. Declare Main Exchange and Queue with DLX args
        self.channel.exchange_declare(exchange=MAIN_EXCHANGE, exchange_type='topic', durable=True)
        
        args = {
            'x-dead-letter-exchange': DLX_NAME,
            'x-dead-letter-routing-key': 'inventory_dlq_key'
        }
        self.channel.queue_declare(queue=MAIN_QUEUE, durable=True, arguments=args)
        
        # 3. Bind OrderCreated events
        # Correction: Use wildcard to match any producer (order.OrderCreated, orders.OrderCreated, etc)
        self.channel.queue_bind(exchange=MAIN_EXCHANGE, queue=MAIN_QUEUE, routing_key="*.OrderCreated")

        # Set QoS
        self.channel.basic_qos(prefetch_count=1)

    def start_consuming(self):
        self.connect()
        # Initialize publisher with the same channel/connection
        publisher = RabbitMQPublisher(host="ignored", channel=self.channel)
        use_case = ReserveInventoryUseCase(self.repository, publisher)

        print(f" [*] Waiting for messages in {MAIN_QUEUE}")

        def callback(ch, method, properties, body):
            print(f" [x] Received {body}")
            try:
                # Local retry logic inside functionality using Tenacity or simple loop
                # The requirement says "messages that cannot be processed after 3 retries" -> DLQ.
                # If we raise Exception here without catching, RabbitMQ will retry indefinitely 
                # unless we manage 'requeue'.
                # To implement "3 retries then DLQ", we try-catch up to 3 times here.
                
                self._process_message_with_retries(use_case, body)
                
                # If successful, Ack
                ch.basic_ack(delivery_tag=method.delivery_tag)
            
            except Exception as e:
                print(f" [!] Failed to process after retries: {e}")
                # Nack with requeue=False sends it to DLX (because of x-dead-letter-exchange)
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        self.channel.basic_consume(queue=MAIN_QUEUE, on_message_callback=callback)
        self.channel.start_consuming()

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1), reraise=True)
    def _process_message_with_retries(self, use_case, body):
        data = json.loads(body)
        event_data = data.get("data")
        
        order_id = event_data.get("order_id")
        items = event_data.get("items")
        
        use_case.execute(order_id, items)

if __name__ == "__main__":
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
    # Correct connection string builder
    AMQP_URL = f"amqp://user:password@{RABBITMQ_HOST}:5672/%2f"
    
    # We rely on main.py to inject repo, but for standalone run we might Mock or init here
    pass
