"""Adaptador de persistencia PostgreSQL para Inventory Service"""
import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Optional, Generator

from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import QueuePool

from ...domain.models import Product
from ...domain.ports import InventoryRepository

logger = logging.getLogger(__name__)
Base = declarative_base()


class ProductModel(Base):
    """Modelo SQLAlchemy para productos"""
    __tablename__ = "products"
    
    product_id = Column(String, primary_key=True)
    stock = Column(Integer, nullable=False, default=0)


class ProcessedOrderModel(Base):
    """Modelo SQLAlchemy para órdenes procesadas (idempotencia)"""
    __tablename__ = "processed_orders_inventory"
    
    order_id = Column(String, primary_key=True)
    status = Column(String, nullable=False)
    processed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class PostgresInventoryRepository(InventoryRepository):
    """Implementación del repositorio de inventario con PostgreSQL"""
    
    def __init__(self, db_url: str):
        self.engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True
        )
        Base.metadata.create_all(self.engine)
        self._session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        self._seed_data()
        logger.info("PostgresInventoryRepository inicializado")

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

    def _seed_data(self) -> None:
        """Inicializa datos de prueba si no existen"""
        with self._get_session() as session:
            if session.query(ProductModel).count() == 0:
                products = [
                    ProductModel(product_id="prod_1", stock=100),
                    ProductModel(product_id="prod_2", stock=50),
                    ProductModel(product_id="prod-001", stock=100),
                    ProductModel(product_id="prod-002", stock=50)
                ]
                session.add_all(products)
                logger.info("Datos de prueba inicializados")

    def get_product(self, product_id: str) -> Optional[Product]:
        """Obtiene un producto por su ID"""
        with self._get_session() as session:
            model = session.query(ProductModel).filter_by(product_id=product_id).first()
            if model:
                return Product(product_id=model.product_id, stock=model.stock)
            return None

    def update_stock(self, product_id: str, quantity: int) -> None:
        """Actualiza el stock de un producto"""
        with self._get_session() as session:
            product = session.query(ProductModel).filter_by(product_id=product_id).first()
            if product:
                product.stock += quantity
                logger.debug(f"Stock actualizado: {product_id} -> {product.stock}")
            else:
                logger.warning(f"Producto no encontrado: {product_id}")

    def is_order_processed(self, order_id: str) -> bool:
        """Verifica si una orden ya fue procesada"""
        with self._get_session() as session:
            return session.query(ProcessedOrderModel).filter_by(order_id=order_id).first() is not None

    def mark_order_processed(self, order_id: str, status: str) -> None:
        """Marca una orden como procesada"""
        with self._get_session() as session:
            record = ProcessedOrderModel(order_id=order_id, status=status)
            session.add(record)
            logger.info(f"Orden {order_id} marcada como {status}")
