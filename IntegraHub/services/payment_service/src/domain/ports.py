"""Puertos (interfaces) de dominio - Payment Service"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from .models import PaymentTransaction


class PaymentGateway(ABC):
    """Puerto de salida para el gateway de pagos externo"""

    @abstractmethod
    def charge(self, order_id: str, amount: float) -> str:
        """
        Intenta cobrar el monto especificado.

        Args:
            order_id: ID de la orden
            amount: Monto a cobrar

        Returns:
            str: ID de la transacción si es exitosa

        Raises:
            Exception: Si el pago falla por cualquier razón
        """
        pass


class EventPublisher(ABC):
    """Puerto de salida para publicación de eventos"""

    @abstractmethod
    def publish(self, topic: str, event_type: str, data: Dict[str, Any]) -> None:
        """Publica un evento en el bus de mensajes"""
        pass
