"""Puertos (interfaces) de dominio - Notification Service"""

from abc import ABC, abstractmethod
from typing import Optional


class NotificationChannel(ABC):
    """Puerto de salida para canales de notificación"""

    @abstractmethod
    def send(self, message: str, recipient: Optional[str] = None) -> None:
        """
        Envía un mensaje a través del canal.

        Args:
            message: Cuerpo de la notificación
            recipient: Destinatario opcional (email, canal de Slack, etc.)
        """
        pass
