"""Notification Service - Infrastructure Layer Entry Point"""
import logging
import sys

from shared.infrastructure.config import get_rabbitmq_config
from .adapters.notification_channels import SlackAdapter, EmailAdapter
from .adapters.rabbitmq_consumer import RabbitMQConsumer
from ..application.services import NotificationUseCase

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Punto de entrada del Notification Service"""
    logger.info("Iniciando Notification Service...")
    
    # Obtener configuración centralizada
    rabbitmq_config = get_rabbitmq_config()
    
    try:
        # 1. Inicializar adaptadores de canales
        slack_channel = SlackAdapter()
        email_channel = EmailAdapter()
        logger.info("Canales de notificación inicializados")

        # 2. Inicializar caso de uso con lista de canales (Fanout Pub/Sub)
        use_case = NotificationUseCase(channels=[slack_channel, email_channel])

        # 3. Inicializar consumidor
        consumer = RabbitMQConsumer(
            amqp_url=rabbitmq_config.url,
            use_case=use_case
        )
        logger.info("Consumidor RabbitMQ inicializado")

        # 4. Iniciar consumo de mensajes
        logger.info("Iniciando consumo de mensajes...")
        consumer.start_consuming()
        
    except KeyboardInterrupt:
        logger.info("Servicio detenido por el usuario")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error crítico en Notification Service: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
