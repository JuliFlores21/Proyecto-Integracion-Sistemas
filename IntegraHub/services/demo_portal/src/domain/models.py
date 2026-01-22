from dataclasses import dataclass
from typing import List, Optional

@dataclass
class DemoOrder:
    order_id: str
    status: str
    total: float
    correlation_id: Optional[str] = "N/A"

@dataclass
class SystemHealth:
    service_name: str
    status: str # "UP", "DOWN"
    url: str
