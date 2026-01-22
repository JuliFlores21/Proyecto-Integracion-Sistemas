"""Puertos (interfaces) de dominio - Inventory Service"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from .models import Product


class InventoryRepository(ABC):
    """Puerto de salida para persistencia de inventario"""

    @abstractmethod
    def get_product(self, product_id: str) -> Optional[Product]:
        """Obtiene un producto por su ID"""
        pass

    @abstractmethod
    def update_stock(self, product_id: str, quantity: int) -> None:
        """Actualiza el stock de un producto (positivo para añadir, negativo para restar)"""
        pass

    @abstractmethod
    def is_order_processed(self, order_id: str) -> bool:
        """Verifica si una orden ya fue procesada (idempotencia)"""
        pass

    @abstractmethod
    def mark_order_processed(self, order_id: str, status: str) -> None:
        """Marca una orden como procesada con un estado"""
        pass


class EventPublisher(ABC):
    """Puerto de salida para publicación de eventos"""

    @abstractmethod
    def publish(self, topic: str, event_type: str, data: Dict[str, Any]) -> None:
        """Publica un evento en el bus de mensajes"""
        pass
