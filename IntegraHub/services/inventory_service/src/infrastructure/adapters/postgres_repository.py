from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from ...domain.models import Product
from ...domain.ports import InventoryRepository

Base = declarative_base()

class ProductModel(Base):
    __tablename__ = "products"
    product_id = Column(String, primary_key=True)
    stock = Column(Integer)
    # Additional fields can be added as needed
class ProcessedOrderModel(Base):
    __tablename__ = "processed_orders_inventory"
    order_id = Column(String, primary_key=True)
    status = Column(String)
    processed_at = Column(DateTime, default=datetime.utcnow)
# Inventory Repository Implementation
class PostgresInventoryRepository(InventoryRepository):
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self._seed_data()

    def _seed_data(self):
        """Seed some dummy products for testing"""
        session = self.Session()
        if session.query(ProductModel).count() == 0:
            p1 = ProductModel(product_id="prod_1", stock=100)
            p2 = ProductModel(product_id="prod_2", stock=50)
            session.add_all([p1, p2])
            session.commit()
        session.close()

    def get_product(self, product_id: str):
        session = self.Session()
        try:
            model = session.query(ProductModel).filter_by(product_id=product_id).first()
            if model:
                return Product(product_id=model.product_id, stock=model.stock)
            return None
        finally:
            session.close()

    def update_stock(self, product_id: str, quantity: int):
        session = self.Session()
        try:
            product = session.query(ProductModel).filter_by(product_id=product_id).first()
            if product:
                product.stock += quantity
                session.commit()
        finally:
            session.close()

    def is_order_processed(self, order_id: str) -> bool:
        session = self.Session()
        try:
            return session.query(ProcessedOrderModel).filter_by(order_id=order_id).first() is not None
        finally:
            session.close()

    def mark_order_processed(self, order_id: str, status: str):
        session = self.Session()
        try:
            record = ProcessedOrderModel(order_id=order_id, status=status)
            session.add(record)
            session.commit()
        finally:
            session.close()
