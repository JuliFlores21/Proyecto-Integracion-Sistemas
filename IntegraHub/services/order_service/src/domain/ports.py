from abc import ABC, abstractmethod
from typing import Optional
from .models import Order

class OrderRepository(ABC):
    @abstractmethod
    def save(self, order: Order) -> Order:
        pass

    @abstractmethod
    def get_by_id(self, order_id: str) -> Optional[Order]:
        pass
    
    @abstractmethod
    def exists_idempotency_key(self, key: str) -> bool:
        pass
    
    @abstractmethod
    def save_idempotency_key(self, key: str, order_id: str):
        pass

class EventPublisher(ABC):
    @abstractmethod
    def publish(self, topic: str, event_type: str, data: dict):
        pass
