# Application Layer (Use Cases)
# Este módulo contiene la orquestación del negocio (casos de uso).
# No conoce detalles de infraestructura (DB/RabbitMQ); depende de puertos (interfaces) del dominio.
 

from ..domain.models import Order, OrderItem
from ..domain.ports import OrderRepository, EventPublisher

class CreateOrderUseCase:
    def __init__(self, repository: OrderRepository, publisher: EventPublisher):
        # repository: Port para persistencia (implementado en infraestructura)
        # publisher: Port para publicación de eventos (implementado en infraestructura)
        self.repository = repository
        self.publisher = publisher

    def execute(self, customer_id: str, items_data: list, idempotency_key: str = None) -> Order:
        # Idempotency Check:
        # Se aplica idempotencia en la API usando un key externo (X-Idempotency-Key).
        # Evita duplicados si el cliente reintenta la misma solicitud por timeout/red.

        if idempotency_key and self.repository.exists_idempotency_key(idempotency_key):
            raise ValueError(f"Order with idempotency key {idempotency_key} already processed.")

        # Logic
        # Construcción del agregado Order desde DTOs (sin FastAPI/Pydantic aquí).
        # Domain Models deben permanecer libres de frameworks de infraestructura.
        order_items = [OrderItem(**item) for item in items_data]
        order = Order(customer_id=customer_id, items=order_items)
        
        # Persistencia vía Port (OrderRepository)
        saved_order = self.repository.save(order)
        if idempotency_key:
            # Guardamos el idempotency key para evitar reprocesar la misma orden.
            self.repository.save_idempotency_key(idempotency_key, saved_order.order_id)

        # Publicación de evento de integración:
        # - topic: "orders"
        # - event_type: "OrderCreated"
        # El payload contiene los campos necesarios para servicios consumidores (payment/inventory/notification).
        event_payload = {
            "order_id": saved_order.order_id,
            "customer_id": saved_order.customer_id,
            "total_amount": saved_order.total_amount,
            "items": [{"product_id": i.product_id, "quantity": i.quantity} for i in saved_order.items],
            "status": saved_order.status
        }
        
        # Event Publisher Port: desacopla el caso de uso del broker (RabbitMQ).
        self.publisher.publish("orders", "OrderCreated", event_payload)
        
        return saved_order

class UpdateOrderStatusUseCase:
    def __init__(self, repository: OrderRepository):
        # Caso de uso para sincronizar el estado de la orden
        # desde eventos externos (OrderConfirmed / OrderRejected).
        self.repository = repository

    def execute(self, order_id: str, status: str):
        # Actualización simple delegada al repositorio.
        self.repository.update_status(order_id, status)
