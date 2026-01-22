"""Adaptador de persistencia PostgreSQL para Order Service"""

import logging
from contextlib import contextmanager
from typing import Optional, Generator

from sqlalchemy import (
    create_engine,
    Column,
    String,
    Float,
    Integer,
    ForeignKey,
    DateTime,
)
from sqlalchemy.orm import sessionmaker, relationship, Session, declarative_base
from sqlalchemy.pool import QueuePool

from ...domain.models import Order, OrderItem, OrderStatus
from ...domain.ports import OrderRepository

logger = logging.getLogger(__name__)
Base = declarative_base()


class OrderModel(Base):
    """Modelo SQLAlchemy para la tabla orders"""

    __tablename__ = "orders"

    order_id = Column(String, primary_key=True)
    customer_id = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False)
    total_amount = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False)
    items = relationship(
        "OrderItemModel", back_populates="order", cascade="all, delete-orphan"
    )


class OrderItemModel(Base):
    """Modelo SQLAlchemy para la tabla order_items"""

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(
        String, ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False
    )
    product_id = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    order = relationship("OrderModel", back_populates="items")


class IdempotencyModel(Base):
    """Modelo SQLAlchemy para claves de idempotencia"""

    __tablename__ = "idempotency_keys"

    key = Column(String, primary_key=True)
    order_id = Column(String, nullable=False)


class PostgresOrderRepository(OrderRepository):
    """Implementación del repositorio de órdenes con PostgreSQL"""

    def __init__(self, db_url: str):
        self.engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
        Base.metadata.create_all(self.engine)
        self._session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        logger.info("PostgresOrderRepository inicializado")

    @contextmanager
    def _get_session(self) -> Generator[Session, None, None]:
        """Context manager para manejo seguro de sesiones"""
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error en sesión de base de datos: {e}")
            raise
        finally:
            session.close()

    def save(self, order: Order) -> Order:
        """Persiste una orden en la base de datos"""
        with self._get_session() as session:
            db_order = OrderModel(
                order_id=order.order_id,
                customer_id=order.customer_id,
                status=(
                    order.status.value
                    if isinstance(order.status, OrderStatus)
                    else order.status
                ),
                total_amount=order.total_amount,
                created_at=order.created_at,
            )
            for item in order.items:
                db_item = OrderItemModel(
                    product_id=item.product_id, quantity=item.quantity, price=item.price
                )
                db_order.items.append(db_item)

            session.add(db_order)
            logger.info(f"Orden {order.order_id} guardada en base de datos")
        return order

    def get_by_id(self, order_id: str) -> Optional[Order]:
        """Obtiene una orden por su ID"""
        with self._get_session() as session:
            db_order = session.query(OrderModel).filter_by(order_id=order_id).first()
            if not db_order:
                return None

            items = [
                OrderItem(
                    product_id=item.product_id, quantity=item.quantity, price=item.price
                )
                for item in db_order.items
            ]
            return Order(
                customer_id=db_order.customer_id,
                items=items,
                status=OrderStatus(db_order.status),
                order_id=db_order.order_id,
                created_at=db_order.created_at,
            )

    def list_orders(self) -> list[Order]:
        """Lista las últimas 20 órdenes"""
        with self._get_session() as session:
            db_orders = (
                session.query(OrderModel)
                .order_by(OrderModel.created_at.desc())
                .limit(20)
                .all()
            )
            orders = []
            for db_order in db_orders:
                items = [
                    OrderItem(
                        product_id=item.product_id,
                        quantity=item.quantity,
                        price=item.price,
                    )
                    for item in db_order.items
                ]
                orders.append(
                    Order(
                        customer_id=db_order.customer_id,
                        items=items,
                        status=OrderStatus(db_order.status),
                        order_id=db_order.order_id,
                        created_at=db_order.created_at,
                    )
                )
            return orders

    def update_status(self, order_id: str, status: str) -> None:
        """Actualiza el estado de una orden"""
        with self._get_session() as session:
            db_order = session.query(OrderModel).filter_by(order_id=order_id).first()
            if db_order:
                db_order.status = status
                session.add(db_order)
                logger.info(f"Estado de orden {order_id} actualizado a {status}")
            else:
                logger.warning(f"Intento de actualizar orden inexistente: {order_id}")

    def exists_idempotency_key(self, key: str) -> bool:
        """Verifica si existe una clave de idempotencia"""
        with self._get_session() as session:
            exists = (
                session.query(IdempotencyModel).filter_by(key=key).first() is not None
            )
            return exists

    def save_idempotency_key(self, key: str, order_id: str) -> None:
        """Guarda una clave de idempotencia"""
        with self._get_session() as session:
            entry = IdempotencyModel(key=key, order_id=order_id)
            session.add(entry)
            logger.debug(f"Clave de idempotencia guardada: {key}")
