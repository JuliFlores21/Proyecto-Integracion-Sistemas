import pika
import json
import uuid
import time
from typing import Callable, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class RabbitMQConnection:
    def __init__(self, host: str, user: str = "user", password: str = "password"):
        self.host = host
        self.credentials = pika.PlainCredentials(user, password)
        self.parameters = pika.ConnectionParameters(host=self.host, credentials=self.credentials)
        self.connection = None
        self.channel = None

    def connect(self):
        if not self.connection or self.connection.is_closed:
            print(f" [RabbitMQ] Connecting to {self.host}...")
            self.connection = pika.BlockingConnection(self.parameters)
            self.channel = self.connection.channel()
            # Restore topology defaults if needed here
            # self.setup_topology()

    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()

    def get_channel(self):
        self.connect()
        return self.channel

class BasePublisher:
    def __init__(self, connection: RabbitMQConnection, exchange_name: str = "integrahub_exchange"):
        self.connection_wrapper = connection
        self.exchange_name = exchange_name

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(pika.exceptions.AMQPConnectionError)
    )
    def publish(self, topic: str, event_type: str, data: dict, correlation_id: str = None):
        channel = self.connection_wrapper.get_channel()
        channel.exchange_declare(exchange=self.exchange_name, exchange_type='topic', durable=True)

        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        message_body = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "timestamp": str(uuid.uuid1()), # simple timestamp
            "data": data,
            "correlation_id": correlation_id
        }

        routing_key = f"{topic}.{event_type}"

        channel.basic_publish(
            exchange=self.exchange_name,
            routing_key=routing_key,
            body=json.dumps(message_body),
            properties=pika.BasicProperties(
                delivery_mode=2,
                correlation_id=correlation_id,
                content_type='application/json'
            )
        )
        print(f" [x] Sent {routing_key} (CorrId: {correlation_id})")

class BaseConsumer:
    """
    Base Consumer with DLQ support and automatic binding.
    """
    def __init__(self, connection: RabbitMQConnection, service_name: str, exchange_name: str = "integrahub_exchange"):
        self.connection_wrapper = connection
        self.service_name = service_name
        self.exchange_name = exchange_name
        
        self.dlx_name = "integrahub_dlx"
        self.dlq_name = f"{service_name}_dlq"
        self.queue_name = f"{service_name}_queue"

    def setup_topology(self):
        channel = self.connection_wrapper.get_channel()

        # 1. Main Exchange
        channel.exchange_declare(exchange=self.exchange_name, exchange_type='topic', durable=True)

        # 2. DLX setup
        channel.exchange_declare(exchange=self.dlx_name, exchange_type='direct', durable=True)
        channel.queue_declare(queue=self.dlq_name, durable=True)
        channel.queue_bind(queue=self.dlq_name, exchange=self.dlx_name, routing_key=f"{self.service_name}_dlq_key")

        # 3. Queue with DLQ config
        args = {
            'x-dead-letter-exchange': self.dlx_name,
            'x-dead-letter-routing-key': f"{self.service_name}_dlq_key"
        }
        channel.queue_declare(queue=self.queue_name, durable=True, arguments=args)
        channel.basic_qos(prefetch_count=1)

    def bind_event(self, routing_key: str):
        channel = self.connection_wrapper.get_channel()
        channel.queue_bind(exchange=self.exchange_name, queue=self.queue_name, routing_key=routing_key)

    def start_consuming(self, callback_function: Callable):
        self.setup_topology()
        channel = self.connection_wrapper.get_channel()

        def wrapper_callback(ch, method, properties, body):
            print(f" [x] Received {method.routing_key} | CorrId: {properties.correlation_id}")
            try:
                # Pass correlation_id in context if needed, currently just logging
                callback_function(json.loads(body), properties.correlation_id)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                print(f" [!] Error processing: {e}")
                # Reject -> DLQ
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        print(f" [*] Waiting for messages in {self.queue_name}")
        channel.basic_consume(queue=self.queue_name, on_message_callback=wrapper_callback)
        channel.start_consuming()
