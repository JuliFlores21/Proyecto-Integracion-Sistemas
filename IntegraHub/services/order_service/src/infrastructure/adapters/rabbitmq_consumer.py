# Infrastructure Adapter: RabbitMQ Consumer (Inbound)
# Este consumidor escucha eventos externos que impactan el estado de una orden.
# Ej: OrderConfirmed / OrderRejected publicados por payment/inventory.

import pika
import json
import threading
from ...application.services import UpdateOrderStatusUseCase
from ...domain.ports import OrderRepository

MAIN_EXCHANGE = "integrahub_exchange"
PROCESS_QUEUE = "order_updates_queue"

class RabbitMQConsumer:
    def __init__(self, amqp_url: str, repository: OrderRepository):
        self.amqp_url = amqp_url
        self.repository = repository
        self.connection = None
        self.channel = None
        self._thread = None
        self._stop_event = threading.Event()

    def connect(self):
        params = pika.URLParameters(self.amqp_url)
        self.connection = pika.BlockingConnection(params)
        self.channel = self.connection.channel()

        # Declare Exchange (Idempotent)
        self.channel.exchange_declare(exchange=MAIN_EXCHANGE, exchange_type='topic', durable=True)
        
        # Declare Queue
        self.channel.queue_declare(queue=PROCESS_QUEUE, durable=True)
        
        # Bindings for status updates
        # We listen to events that affect order status
        self.channel.queue_bind(exchange=MAIN_EXCHANGE, queue=PROCESS_QUEUE, routing_key="*.OrderConfirmed")
        self.channel.queue_bind(exchange=MAIN_EXCHANGE, queue=PROCESS_QUEUE, routing_key="*.OrderRejected")
        # Could also bind to 'inventory.OrderRejected' explicitely if needed, but wildcard covers it if consistent naming.
        # Actually Inventory publishes 'inventory.OrderRejected' or 'inventory.InventoryReserved' (which is not confirmation yet)
        # Payment publishes 'payments.OrderConfirmed' or 'payments.OrderRejected'
        
        # Bindings:
        # - "*.OrderConfirmed" y "*.OrderRejected" permiten recibir desde cualquier emisor
        #   (payment_service, inventory_service, etc.) manteniendo bajo acoplamiento.
  
        # Nota: este servicio no publica aquí; solo consume y actualiza DB local.

        # NOTE: If we want to capture Inventory Rejection specifically if Payment is not reached.
        # Inventory failure publishes "OrderRejected" so it matches *.OrderRejected.

    def start_in_background(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        try:
            self.connect()
            # Use Case: actualización de estado (application layer)
            use_case = UpdateOrderStatusUseCase(self.repository)
            
            print(f" [*] Order Service Consumer waiting for status updates in {PROCESS_QUEUE}")

            def callback(ch, method, properties, body):
                try:
                    # El evento sigue el contrato: { event_type, data, correlation_id, ... }
                    data = json.loads(body)
                    event_type = data.get("event_type")
                    event_data = data.get("data", {})
                    order_id = event_data.get("order_id")
                    
                    # Mapeo de evento -> estado interno del dominio
                    # - OrderConfirmed => CONFIRMED
                    # - OrderRejected => REJECTED
                    new_status = None
                    if event_type == "OrderConfirmed":
                        new_status = "CONFIRMED"
                    elif event_type == "OrderRejected":
                        new_status = "REJECTED"
                        # reason = event_data.get("reason")
                    
                    if order_id and new_status:
                        print(f" [x] Updating Order {order_id} to {new_status}")
                        use_case.execute(order_id, new_status)
                    
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as e:
                    print(f" [!] Error processing status update: {e}")
                    # In a robust system, DLQ here. For now, simple nack without requeue or similar.
                    # Si falla, se hace NACK sin requeue para evitar loop infinito.
                    # En una versión robusta, se configura DLQ (o usar BaseConsumer del shared).
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            self.channel.basic_consume(queue=PROCESS_QUEUE, on_message_callback=callback)
            self.channel.start_consuming()
            
        except Exception as e:
            print(f" [!] Order Consumer failed: {e}")

    def stop(self):
        if self.connection and self.connection.is_open:
            self.connection.close()
