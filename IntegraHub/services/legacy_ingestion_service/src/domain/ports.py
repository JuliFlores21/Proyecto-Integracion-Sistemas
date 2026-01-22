from abc import ABC, abstractmethod
from typing import List
from .models import LegacyProduct

class InventoryRepository(ABC):
    @abstractmethod
    def upsert_bulk(self, products: List[LegacyProduct]):
        """
        Inserts or Updates (if exists) a list of products.
        """
        pass
