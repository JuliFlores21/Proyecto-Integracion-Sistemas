from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any

@dataclass
class DomainEvent:
    event_id: str
    event_type: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: str = ""
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "data": self.data
        }

# Specific Schemas (Reference)

@dataclass
class OrderCreatedEvent(DomainEvent):
    event_type: str = "OrderCreated"

@dataclass
class OrderConfirmedEvent(DomainEvent):
    event_type: str = "OrderConfirmed"

@dataclass
class OrderRejectedEvent(DomainEvent):
    event_type: str = "OrderRejected"
