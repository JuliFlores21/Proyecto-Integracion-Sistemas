from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from .models import Product

class InventoryRepository(ABC):
    @abstractmethod
    def get_product(self, product_id: str) -> Optional[Product]:
        pass

    @abstractmethod
    def update_stock(self, product_id: str, quantity: int):
        pass

    @abstractmethod
    def is_order_processed(self, order_id: str) -> bool:
        pass

    @abstractmethod
    def mark_order_processed(self, order_id: str, status: str):
        pass

class EventPublisher(ABC):
    @abstractmethod
    def publish(self, topic: str, event_type: str, data: dict):
        pass
