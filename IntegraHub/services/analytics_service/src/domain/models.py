from dataclasses import dataclass
from datetime import datetime

@dataclass
class DailyMetrics:
    date: datetime.date
    total_sales_amount: float
    total_orders_count: int
    rejected_orders_count: int
    last_updated: datetime = datetime.utcnow()
