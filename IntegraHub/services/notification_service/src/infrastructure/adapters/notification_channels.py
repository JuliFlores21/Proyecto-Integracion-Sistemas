"""Adaptadores de canales de notificación"""

import logging
from typing import Optional

from ...domain.ports import NotificationChannel

logger = logging.getLogger(__name__)


class SlackAdapter(NotificationChannel):
    """Adaptador para enviar notificaciones a Slack (simulado)"""

    def send(self, message: str, recipient: Optional[str] = "#ops-alerts") -> None:
        """Envía mensaje a canal de Slack"""
        # Simulación de llamada a Webhook de Slack
        logger.info(f"[Slack] 📢 Enviando a {recipient}: {message[:50]}...")
        print(f"   [Slack Webhook] 📢 Posting to {recipient}: {message}")


class EmailAdapter(NotificationChannel):
    """Adaptador para enviar notificaciones por email (simulado)"""

    def send(
        self, message: str, recipient: Optional[str] = "customer@example.com"
    ) -> None:
        """Envía mensaje por email"""
        # Simulación de llamada SMTP
        logger.info(f"[Email] 📧 Enviando a {recipient}")
        print(
            f"   [Email Service] 📧 Sending to {recipient}: \n      Subject: Order Update\n      Body: {message}"
        )
