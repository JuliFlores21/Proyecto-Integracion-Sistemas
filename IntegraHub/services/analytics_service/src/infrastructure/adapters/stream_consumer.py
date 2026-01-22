import pika
import json
import threading
import time
from ...application.services import ProcessEventUseCase

EXCHANGE_NAME = "integrahub_exchange"
QUEUE_NAME = "analytics_stream_queue"

class AnalyticsStreamProcessor:
    """
    Acts as a Stream Processor consuming from the Event Bus.
    Although using RabbitMQ, we handle it as an unbounded stream of events.
    """
    def __init__(self, amqp_url: str, use_case: ProcessEventUseCase):
        self.amqp_url = amqp_url
        self.use_case = use_case
        self.connection = None
        self.channel = None
        self.thread = None
        self.is_running = False

    def start(self):
        self.is_running = True
        self.thread = threading.Thread(target=self._run_consumer)
        self.thread.daemon = True
        self.thread.start()

    def _run_consumer(self):
        print(" [Analytics] Stream Processor Starting...")
        # Connection Retry Loop
        while self.is_running:
            try:
                self._connect_and_consume()
            except Exception as e:
                print(f" [Analytics] Connection lost: {e}. Retrying in 5s...")
                time.sleep(5)

    def _connect_and_consume(self):
        params = pika.URLParameters(self.amqp_url)
        self.connection = pika.BlockingConnection(params)
        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic', durable=True)
        self.channel.queue_declare(queue=QUEUE_NAME, durable=True)

        # "Capture all events" - Binding keys
        self.channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME, routing_key="#")

        def callback(ch, method, properties, body):
            try:
                payload = json.loads(body)
                event_type = payload.get("event_type")
                data = payload.get("data")
                
                # Stream Processing Logic
                self.use_case.execute(event_type, data)
                
            except Exception as e:
                print(f" [Analytics] Error processing frame: {e}")
            
            # Auto-ack for high throughput streaming (At most once / At least once trade-off)
            # For analytics, we often prefer speed here in this demo.
            ch.basic_ack(delivery_tag=method.delivery_tag)

        self.channel.basic_qos(prefetch_count=10) # Process in batches-ish
        self.channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
        self.channel.start_consuming()
