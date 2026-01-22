"""Casos de uso de la capa de aplicación - Payment Service"""

import logging

import pybreaker

from ..domain.ports import PaymentGateway, EventPublisher
from ..domain.models import PaymentTransaction

logger = logging.getLogger(__name__)


class ProcessPaymentUseCase:
    """Caso de uso para procesar pagos"""

    def __init__(self, gateway: PaymentGateway, publisher: EventPublisher):
        self._gateway = gateway
        self._publisher = publisher

    def execute(self, order_id: str, amount: float) -> None:
        """
        Ejecuta el procesamiento de pago para una orden.

        Args:
            order_id: ID de la orden
            amount: Monto a cobrar

        Raises:
            pybreaker.CircuitBreakerError: Si el circuit breaker está abierto
        """
        logger.info(f"Procesando pago para orden: {order_id}, monto: {amount}")

        try:
            # 1. Intentar cobro (protegido por Circuit Breaker en el adaptador)
            transaction_id = self._gateway.charge(order_id, amount)

            # 2. Caso de éxito
            logger.info(f"Pago exitoso: {transaction_id}")
            self._publisher.publish(
                "payments",
                "OrderConfirmed",
                {
                    "order_id": order_id,
                    "status": "CONFIRMED",
                    "transaction_id": transaction_id,
                    "total_amount": amount,
                },
            )

        except pybreaker.CircuitBreakerError:
            # Circuit Breaker abierto - fallo rápido
            logger.warning(f"Circuit Breaker abierto. Pago fallido para {order_id}")
            raise

        except Exception as e:
            # Error de lógica/Gateway (ej: Fondos insuficientes)
            logger.error(f"Pago fallido: {e}")
            self._publisher.publish(
                "payments",
                "OrderRejected",
                {"order_id": order_id, "reason": f"Payment Failed: {str(e)}"},
            )
