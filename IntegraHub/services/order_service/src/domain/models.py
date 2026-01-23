from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import uuid

# Domain Layer (Entities / Value Objects)
# Estas clases representan el modelo de dominio.
# Deben evitar dependencias de frameworks (FastAPI, SQLAlchemy, RabbitMQ).
 
@dataclass
class OrderItem:
    # Ítem de orden (parte del agregado Order)
    product_id: str
    quantity: int
    price: float

@dataclass
class Order:
    # Agregado principal: Order
    customer_id: str
    items: List[OrderItem]
    status: str = "PENDING"
    # order_id generado en dominio: identidad del agregado
    order_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    # created_at generado en dominio: trazabilidad temporal
    created_at: datetime = field(default_factory=datetime.utcnow)
    # total_amount calculado: regla de negocio (suma de items)
    total_amount: float = field(init=False)

    def __post_init__(self):
        # Regla: total = Σ(price * quantity)
        self.total_amount = sum(item.price * item.quantity for item in self.items)

