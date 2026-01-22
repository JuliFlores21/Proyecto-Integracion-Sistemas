"""Casos de uso de la capa de aplicación - Inventory Service"""

import logging
from typing import List, Dict, Any

from ..domain.ports import InventoryRepository, EventPublisher

logger = logging.getLogger(__name__)


class ReserveInventoryUseCase:
    """Caso de uso para reservar inventario de una orden"""

    def __init__(self, repository: InventoryRepository, publisher: EventPublisher):
        self._repository = repository
        self._publisher = publisher

    def execute(self, order_id: str, items: List[Dict[str, Any]]) -> None:
        """
        Ejecuta la reserva de inventario para una orden.

        Args:
            order_id: ID de la orden
            items: Lista de items con product_id y quantity
        """
        logger.info(f"Procesando reserva de inventario para orden: {order_id}")

        # 1. Verificación de idempotencia
        if self._repository.is_order_processed(order_id):
            logger.info(f"Orden {order_id} ya procesada. Omitiendo.")
            return

        # 2. Verificar disponibilidad de stock
        can_fulfill, failed_reason = self._check_stock_availability(items)

        # 3. Ejecutar transacción
        if can_fulfill:
            self._reserve_items(order_id, items)
        else:
            self._reject_order(order_id, failed_reason)

    def _check_stock_availability(
        self, items: List[Dict[str, Any]]
    ) -> tuple[bool, str]:
        """Verifica si hay stock suficiente para todos los items"""
        for item in items:
            product_id = item["product_id"]
            qty = item["quantity"]
            product = self._repository.get_product(product_id)

            if not product:
                return False, f"Producto {product_id} no encontrado"

            if not product.has_sufficient_stock(qty):
                return False, f"Stock insuficiente para producto {product_id}"

        return True, ""

    def _reserve_items(self, order_id: str, items: List[Dict[str, Any]]) -> None:
        """Reserva los items descontando del stock"""
        try:
            # Descontar stock de cada item
            for item in items:
                self._repository.update_stock(item["product_id"], -item["quantity"])

            # Marcar orden como procesada
            self._repository.mark_order_processed(order_id, "RESERVED")

            # Publicar evento de éxito
            self._publisher.publish(
                "inventory", "InventoryReserved", {"order_id": order_id}
            )
            logger.info(f"Inventario reservado para orden {order_id}")

        except Exception as e:
            logger.error(f"Error al reservar inventario: {e}")
            raise

    def _reject_order(self, order_id: str, reason: str) -> None:
        """Rechaza la orden por falta de stock"""
        self._repository.mark_order_processed(order_id, "REJECTED")

        self._publisher.publish(
            "inventory", "OrderRejected", {"order_id": order_id, "reason": reason}
        )
        logger.warning(f"Orden {order_id} rechazada: {reason}")
