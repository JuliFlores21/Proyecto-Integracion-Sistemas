"""Casos de uso de la capa de aplicación - Order Service"""

import logging
from typing import List, Dict, Any, Optional

from ..domain.models import Order, OrderItem
from ..domain.ports import OrderRepository, EventPublisher

logger = logging.getLogger(__name__)


class CreateOrderUseCase:
    """Caso de uso para crear una nueva orden"""

    def __init__(self, repository: OrderRepository, publisher: EventPublisher):
        self._repository = repository
        self._publisher = publisher

    def execute(
        self,
        customer_id: str,
        items_data: List[Dict[str, Any]],
        idempotency_key: Optional[str] = None,
    ) -> Order:
        """
        Ejecuta el caso de uso de creación de orden.

        Args:
            customer_id: ID del cliente
            items_data: Lista de diccionarios con datos de items
            idempotency_key: Clave opcional para garantizar idempotencia

        Returns:
            Order: La orden creada

        Raises:
            ValueError: Si la clave de idempotencia ya fue procesada
        """
        logger.info(f"Iniciando creación de orden para cliente: {customer_id}")

        # Verificación de idempotencia (Patrón Idempotent Consumer)
        if idempotency_key and self._repository.exists_idempotency_key(idempotency_key):
            logger.warning(
                f"Orden con clave de idempotencia {idempotency_key} ya procesada"
            )
            raise ValueError(
                f"Order with idempotency key {idempotency_key} already processed."
            )

        # Crear entidades de dominio
        order_items = [OrderItem(**item) for item in items_data]
        order = Order(customer_id=customer_id, items=order_items)

        # Persistir orden
        saved_order = self._repository.save(order)

        # Guardar clave de idempotencia si existe
        if idempotency_key:
            self._repository.save_idempotency_key(idempotency_key, saved_order.order_id)

        # Construir payload del evento
        event_payload = self._build_event_payload(saved_order)

        # Publicar evento de dominio (Patrón Event-Driven)
        self._publisher.publish("orders", "OrderCreated", event_payload)

        logger.info(f"Orden {saved_order.order_id} creada y evento publicado")
        return saved_order

    @staticmethod
    def _build_event_payload(order: Order) -> Dict[str, Any]:
        """Construye el payload del evento de orden creada"""
        return {
            "order_id": order.order_id,
            "customer_id": order.customer_id,
            "total_amount": order.total_amount,
            "items": [
                {"product_id": item.product_id, "quantity": item.quantity}
                for item in order.items
            ],
            "status": (
                order.status.value if hasattr(order.status, "value") else order.status
            ),
        }
