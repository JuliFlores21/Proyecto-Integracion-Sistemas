# Infrastructure Adapter: Postgres Repository (SQLAlchemy)
# Implementa el Port OrderRepository usando una base relacional (PostgreSQL).
# Esta capa sí puede depender de librerías externas (SQLAlchemy).

from sqlalchemy import create_engine, Column, String, Float, Integer, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from typing import Optional
from ...domain.models import Order, OrderItem
from ...domain.ports import OrderRepository
import os

Base = declarative_base()

class OrderModel(Base):
    __tablename__ = "orders"
    order_id = Column(String, primary_key=True)
    customer_id = Column(String)
    status = Column(String)
    total_amount = Column(Float)
    created_at = Column(DateTime)
    items = relationship("OrderItemModel", back_populates="order")

class OrderItemModel(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String, ForeignKey("orders.order_id"))
    product_id = Column(String)
    quantity = Column(Integer)
    price = Column(Float)
    order = relationship("OrderModel", back_populates="items")

class IdempotencyModel(Base):
    __tablename__ = "idempotency_keys"
    key = Column(String, primary_key=True)
    order_id = Column(String)

class PostgresOrderRepository(OrderRepository):
    def __init__(self, db_url: str):
        # Inicializa engine + crea tablas si no existen (demo-friendly).
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def save(self, order: Order) -> Order:
        # Mapea Domain -> ORM (Order/OrderItem) y persiste.
        session = self.Session()
        try:
            db_order = OrderModel(
                order_id=order.order_id,
                customer_id=order.customer_id,
                status=order.status,
                total_amount=order.total_amount,
                created_at=order.created_at
            )
            for item in order.items:
                db_item = OrderItemModel(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price=item.price
                )
                db_order.items.append(db_item)
            
            session.add(db_order)
            session.commit()
            return order
        finally:
            session.close()

    def get_by_id(self, order_id: str) -> Optional[Order]:
        session = self.Session()
        try:
            db_order = session.query(OrderModel).filter_by(order_id=order_id).first()
            if not db_order:
                return None
            return self._map(db_order)
        finally:
            session.close()

    def get_all(self) -> list[Order]:
        session = self.Session()
        try:
            db_orders = session.query(OrderModel).order_by(OrderModel.created_at.desc()).limit(50).all()
            return [self._map(o) for o in db_orders]
        finally:
            session.close()

    def _map(self, db_order):
        # Mapea ORM -> Domain (manteniendo independencia del dominio).
        order = Order(
            order_id=db_order.order_id,
            customer_id=db_order.customer_id,
            status=db_order.status,
            created_at=db_order.created_at,
            items=[OrderItem(product_id=i.product_id, quantity=i.quantity, price=i.price) for i in db_order.items]
        )
        order.total_amount = db_order.total_amount
        return order
    # Verify idempotency key existence
    def exists_idempotency_key(self, key: str) -> bool:
        # Parte del patrón de idempotencia a nivel API:
        # evita procesar dos veces un POST /orders repetido.
        session = self.Session()
        try:
            return session.query(IdempotencyModel).filter_by(key=key).first() is not None
        finally:
            session.close()

    def save_idempotency_key(self, key: str, order_id: str):
        session = self.Session()
        try:
            entry = IdempotencyModel(key=key, order_id=order_id)
            session.add(entry)
            session.commit()
        finally:
            session.close()
    # Update order status
    def update_status(self, order_id: str, status: str):
        # Operación usada por el consumidor de eventos de estado (OrderConfirmed/OrderRejected).
        session = self.Session()
        try:
            order = session.query(OrderModel).filter_by(order_id=order_id).first()
            if order:
                order.status = status
                session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
