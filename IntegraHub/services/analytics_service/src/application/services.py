"""Casos de uso de la capa de aplicación - Analytics Service"""
import logging
from typing import Dict, Any

from ..domain.ports import MetricsRepository
from ..domain.models import DailyMetrics

logger = logging.getLogger(__name__)


class ProcessEventUseCase:
    """Caso de uso para procesar eventos y actualizar métricas"""
    
    def __init__(self, repository: MetricsRepository):
        self._repository = repository

    def execute(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Procesa un evento y actualiza las métricas correspondientes.
        
        Args:
            event_type: Tipo de evento
            data: Datos del evento
        """
        if event_type == "OrderConfirmed":
            amount = data.get("total_amount", 0.0)
            self._repository.increment_orders(amount)
            logger.info(f"Analytics: Venta registrada +${amount}")

        elif event_type == "OrderRejected":
            self._repository.increment_rejections()
            logger.info("Analytics: Rechazo registrado")
        
        # Eventos adicionales pueden ser procesados aquí
        else:
            logger.debug(f"Evento no procesado para métricas: {event_type}")


class GetMetricsUseCase:
    """Caso de uso para obtener métricas del día"""
    
    def __init__(self, repository: MetricsRepository):
        self._repository = repository
        
    def execute(self) -> DailyMetrics:
        """
        Obtiene las métricas del día actual.
        
        Returns:
            DailyMetrics: Métricas del día
        """
        return self._repository.get_today_metrics()
