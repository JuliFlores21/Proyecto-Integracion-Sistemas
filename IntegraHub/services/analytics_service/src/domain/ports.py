from abc import ABC, abstractmethod
from typing import Optional
from .models import DailyMetrics

class MetricsRepository(ABC):
    @abstractmethod
    def get_today_metrics(self) -> DailyMetrics:
        """Fetch metrics for the current day"""
        pass

    @abstractmethod
    def increment_orders(self, amount: float = 0.0):
        """Update total orders count and sales volume"""
        pass

    @abstractmethod
    def increment_rejections(self):
        """Update rejected count"""
        pass
