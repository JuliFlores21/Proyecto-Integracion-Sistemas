"""Modelos de dominio para Order Service - Capa de Dominio"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List
from enum import Enum
import uuid


class OrderStatus(str, Enum):
    """Estados posibles de una orden"""

    PENDING = "PENDING"
    CREATED = "CREATED"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class OrderItem:
    """Value Object que representa un item de una orden"""

    product_id: str
    quantity: int
    price: float

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("La cantidad debe ser mayor a 0")
        if self.price < 0:
            raise ValueError("El precio no puede ser negativo")

    @property
    def subtotal(self) -> float:
        """Calcula el subtotal del item"""
        return self.price * self.quantity


@dataclass
class Order:
    """Entidad de dominio que representa una Orden"""

    customer_id: str
    items: List[OrderItem]
    status: OrderStatus = OrderStatus.PENDING
    order_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    total_amount: float = field(init=False)

    def __post_init__(self):
        """Calcula el total de la orden después de la inicialización"""
        self.total_amount = sum(item.subtotal for item in self.items)

    def confirm(self) -> None:
        """Confirma la orden"""
        if self.status != OrderStatus.PENDING:
            raise ValueError(f"No se puede confirmar una orden en estado {self.status}")
        self.status = OrderStatus.CONFIRMED

    def reject(self, reason: str = None) -> None:
        """Rechaza la orden"""
        if self.status == OrderStatus.CONFIRMED:
            raise ValueError("No se puede rechazar una orden ya confirmada")
        self.status = OrderStatus.REJECTED
