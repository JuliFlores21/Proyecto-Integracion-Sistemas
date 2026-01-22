from abc import ABC, abstractmethod
from typing import List, Dict
from ..domain.models import DemoOrder, SystemHealth

class OrderServicePort(ABC):
    @abstractmethod
    def create_demo_order(self, customer_id: str, items: List[Dict]) -> str:
        pass

    @abstractmethod
    def get_orders(self) -> List[DemoOrder]:
        pass

class SystemStatusPort(ABC):
    @abstractmethod
    def check_health(self) -> List[SystemHealth]:
        pass
