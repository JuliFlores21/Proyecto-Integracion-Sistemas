from ..domain.models import Order, OrderItem
from ..domain.ports import OrderRepository, EventPublisher

class CreateOrderUseCase:
    def __init__(self, repository: OrderRepository, publisher: EventPublisher):
        self.repository = repository
        self.publisher = publisher

    def execute(self, customer_id: str, items_data: list, idempotency_key: str = None) -> Order:
        # Idempotency Check (Idempotent Consumer Pattern applied to API)
        if idempotency_key and self.repository.exists_idempotency_key(idempotency_key):
            raise ValueError(f"Order with idempotency key {idempotency_key} already processed.")

        # Logic
        order_items = [OrderItem(**item) for item in items_data]
        order = Order(customer_id=customer_id, items=order_items)
        
        # Persistence
        saved_order = self.repository.save(order)
        if idempotency_key:
            self.repository.save_idempotency_key(idempotency_key, saved_order.order_id)

        # Publish Event
        event_payload = {
            "order_id": saved_order.order_id,
            "customer_id": saved_order.customer_id,
            "total_amount": saved_order.total_amount,
            "items": [{"product_id": i.product_id, "quantity": i.quantity} for i in saved_order.items],
            "status": saved_order.status
        }
        
        # The prompt mentioned "Retry with Backoff for communication with payment service".
        # Since the flow is API -> Event -> ..., the 'communication' is effectively publishing the event 
        # that the Payment Service will eventually consume.
        self.publisher.publish("orders", "OrderCreated", event_payload)
        
        return saved_order
