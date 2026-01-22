from dataclasses import dataclass
from datetime import datetime

@dataclass
class PaymentTransaction:
    order_id: str
    status: str
    amount: float
    provider_transaction_id: str = ""
    timestamp: datetime = datetime.utcnow()
