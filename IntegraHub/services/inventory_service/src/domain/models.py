"""Modelos de dominio para Inventory Service"""

from dataclasses import dataclass
from enum import Enum


class TransactionStatus(str, Enum):
    """Estados posibles de una transacción de inventario"""

    RESERVED = "RESERVED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"


@dataclass(frozen=True)
class Product:
    """Entidad de dominio que representa un Producto"""

    product_id: str
    stock: int

    def has_sufficient_stock(self, quantity: int) -> bool:
        """Verifica si hay stock suficiente"""
        return self.stock >= quantity


@dataclass
class OrderTransaction:
    """Value Object que representa una transacción de orden procesada"""

    order_id: str
    status: TransactionStatus
