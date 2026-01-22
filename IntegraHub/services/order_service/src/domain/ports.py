from abc import ABC, abstractmethod
from typing import Optional
from .models import Order

# Domain Ports (Interfaces)
# Definen contratos que la infraestructura debe implementar.
# Permiten inversión de dependencias (Hexagonal Architecture).
 
class OrderRepository(ABC):
    """Port de persistencia: define operaciones mínimas para almacenar y consultar órdenes."""
    @abstractmethod
    def save(self, order: Order) -> Order:
        pass

    @abstractmethod
    def get_by_id(self, order_id: str) -> Optional[Order]:
        pass

    @abstractmethod
    def get_all(self) -> list[Order]:
        pass
    
    @abstractmethod
    def exists_idempotency_key(self, key: str) -> bool:
        """Verifica si una solicitud ya fue procesada (idempotencia a nivel API)."""
        pass
    
    @abstractmethod
    def save_idempotency_key(self, key: str, order_id: str):
        """Registra la clave de idempotencia asociada a una orden."""
        pass

    @abstractmethod
    def update_status(self, order_id: str, status: str):
        """Actualiza el estado de una orden (p.ej. CONFIRMED/REJECTED)."""
        pass

class EventPublisher(ABC):
    """Port de mensajería: publica eventos de integración sin acoplarse al broker."""
    @abstractmethod
    def publish(self, topic: str, event_type: str, data: dict):
        pass
