"""Casos de uso de la capa de aplicación - Notification Service"""
import logging
from typing import List, Dict, Any

from ..domain.ports import NotificationChannel

logger = logging.getLogger(__name__)


class MessageTranslator:
    """
    Implementa el patrón Message Translator.
    Convierte eventos de dominio en mensajes legibles para usuarios.
    """
    
    _TEMPLATES = {
        "OrderCreated": (
            "🆕 Nuevo Pedido Recibido! ID: {order_id}. "
            "Total: ${total_amount}. Esperando procesamiento."
        ),
        "OrderConfirmed": (
            "✅ Pedido {order_id} Confirmado! "
            "Pago exitoso (Txn: {transaction_id}). Preparando envío."
        ),
        "OrderRejected": (
            "❌ Pedido {order_id} Fallido. "
            "Razón: {reason}. Por favor revise los logs del sistema."
        ),
    }
    
    @classmethod
    def translate(cls, event_type: str, data: Dict[str, Any]) -> str:
        """
        Traduce un evento de dominio a un mensaje legible.
        
        Args:
            event_type: Tipo de evento
            data: Datos del evento
            
        Returns:
            str: Mensaje formateado para usuarios
        """
        order_id = data.get("order_id", "Desconocido")
        
        template = cls._TEMPLATES.get(event_type)
        if template:
            return template.format(
                order_id=order_id,
                total_amount=data.get("total_amount", 0),
                transaction_id=data.get("transaction_id", "N/A"),
                reason=data.get("reason", "Razón desconocida")
            )
        
        return f"ℹ️ Actualización de Pedido {order_id}: {event_type}"


class NotificationUseCase:
    """Caso de uso para enviar notificaciones multicanal"""
    
    def __init__(self, channels: List[NotificationChannel]):
        self._channels = channels
        self._translator = MessageTranslator()

    def execute(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Ejecuta el envío de notificaciones a todos los canales.
        
        Args:
            event_type: Tipo de evento
            data: Datos del evento
        """
        # 1. Traducir mensaje
        human_message = self._translator.translate(event_type, data)
        
        # 2. Fan-out a todos los canales (patrón Pub/Sub interno)
        logger.info(f"Broadcast de notificación: '{human_message[:50]}...'")
        
        for channel in self._channels:
            try:
                channel.send(human_message)
            except Exception as e:
                logger.error(
                    f"Error enviando a canal {channel.__class__.__name__}: {e}"
                )
