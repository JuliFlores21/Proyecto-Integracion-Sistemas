import pika
import json
import pybreaker
from ...application.services import ProcessPaymentUseCase
from ...domain.ports import PaymentGateway
from .rabbitmq_publisher import RabbitMQPublisher
from .mock_payment_gateway import MockPaymentGateway

DLX_NAME = "integrahub_dlx"
DLQ_NAME = "payment_dlq"
MAIN_EXCHANGE = "integrahub_exchange"
MAIN_QUEUE = "payment_queue"

class RabbitMQConsumer:
    def __init__(self, amqp_url: str):
        self.amqp_url = amqp_url
        self.connection = None
        self.channel = None
        # Dependencies
        self.gateway = MockPaymentGateway()

    def connect(self):
        params = pika.URLParameters(self.amqp_url)
        self.connection = pika.BlockingConnection(params)
        self.channel = self.connection.channel()

        # 1. Topology
        self.channel.exchange_declare(exchange=DLX_NAME, exchange_type='direct', durable=True)
        self.channel.queue_declare(queue=DLQ_NAME, durable=True)
        self.channel.queue_bind(queue=DLQ_NAME, exchange=DLX_NAME, routing_key="payment_dlq_key")

        self.channel.exchange_declare(exchange=MAIN_EXCHANGE, exchange_type='topic', durable=True)
        
        args = {
            'x-dead-letter-exchange': DLX_NAME,
            'x-dead-letter-routing-key': 'payment_dlq_key'
        }
        self.channel.queue_declare(queue=MAIN_QUEUE, durable=True, arguments=args)
        
        # 2. Bind - Listen to InventoryReserved
        self.channel.queue_bind(exchange=MAIN_EXCHANGE, queue=MAIN_QUEUE, routing_key="inventory.InventoryReserved")
        
        self.channel.basic_qos(prefetch_count=1)

    def start_consuming(self):
        self.connect()
        publisher = RabbitMQPublisher(channel=self.channel)
        use_case = ProcessPaymentUseCase(self.gateway, publisher)

        print(f" [*] Waiting for messages in {MAIN_QUEUE}")

        def callback(ch, method, properties, body):
            print(f" [x] Received {body}")
            try:
                data = json.loads(body)
                # Extract needed data. 
                # Note: InventoryReserved might not contain amount if it wasn't passed down.
                # Assuming the event chain carries E2E context or we query Order Service.
                # For this implementation, we assume Inventory Service passed the original order data inside 'data'
                # OR we Mock the amount if missing just to demonstrate the Payment Logic.
                
                event_data = data.get("data", {})
                order_id = event_data.get("order_id")
                
                # Hack: In a real system, InventoryReserved usually echoes the full order 
                # or we fetch Order details. To stick to P2P flow without extra lookups:
                # We assume 'total_amount' is somehow propagated or we fake it.
                amount = event_data.get("total_amount", 100.0) 

                use_case.execute(order_id, amount)
                ch.basic_ack(delivery_tag=method.delivery_tag)

            except pybreaker.CircuitBreakerError:
                print(" [!] Circuit Breaker OPEN. Rejecting message to DLQ.")
                # Rejecting without requeue sends to DLQ
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            except Exception as e:
                print(f" [!] Unexpected error: {e}")
                # For non-circuit errors (e.g. malformed JSON), also DLQ or retry
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        self.channel.basic_consume(queue=MAIN_QUEUE, on_message_callback=callback)
        self.channel.start_consuming()
