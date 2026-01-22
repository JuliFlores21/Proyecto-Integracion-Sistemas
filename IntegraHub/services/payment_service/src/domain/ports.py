from abc import ABC, abstractmethod
from typing import Optional
from .models import PaymentTransaction

class PaymentGateway(ABC):
    @abstractmethod
    def charge(self, order_id: str, amount: float) -> str:
        """
        Attempts to charge the amount.
        Returns a transaction ID if successful.
        Raises specific exceptions on failure.
        """
        pass

class EventPublisher(ABC):
    @abstractmethod
    def publish(self, topic: str, event_type: str, data: dict):
        pass
