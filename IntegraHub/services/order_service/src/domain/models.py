from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import uuid

@dataclass
class OrderItem:
    product_id: str
    quantity: int
    price: float

@dataclass
class Order:
    customer_id: str
    items: List[OrderItem]
    status: str = "PENDING"
    order_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    total_amount: float = field(init=False)

    def __post_init__(self):
        self.total_amount = sum(item.price * item.quantity for item in self.items)
