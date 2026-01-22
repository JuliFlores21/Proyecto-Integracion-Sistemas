"""Puertos (interfaces) de dominio - Arquitectura Hexagonal"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from .models import Order


class OrderRepository(ABC):
    """Puerto de salida para persistencia de órdenes"""

    @abstractmethod
    def save(self, order: Order) -> Order:
        """Persiste una orden en el repositorio"""
        pass

    @abstractmethod
    def get_by_id(self, order_id: str) -> Optional[Order]:
        """Obtiene una orden por su ID"""
        pass

    @abstractmethod
    def list_orders(self) -> list[Order]:
        """Lista las últimas órdenes"""
        pass

    @abstractmethod
    def update_status(self, order_id: str, status: str) -> None:
        """Actualiza el estado de una orden"""
        pass

    @abstractmethod
    def exists_idempotency_key(self, key: str) -> bool:
        """Verifica si existe una clave de idempotencia"""
        pass

    @abstractmethod
    def save_idempotency_key(self, key: str, order_id: str) -> None:
        """Guarda una clave de idempotencia asociada a una orden"""
        pass


class EventPublisher(ABC):
    """Puerto de salida para publicación de eventos de dominio"""

    @abstractmethod
    def publish(self, topic: str, event_type: str, data: Dict[str, Any]) -> None:
        """Publica un evento en el bus de mensajes"""
        pass
