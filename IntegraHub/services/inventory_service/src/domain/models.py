from dataclasses import dataclass

@dataclass
class Product:
    product_id: str
    stock: int

@dataclass
class OrderTransaction:
    order_id: str
    status: str
