"""Payment Service - Infrastructure Layer Entry Point"""

import logging
import sys

from shared.infrastructure.config import get_rabbitmq_config
from .adapters.rabbitmq_consumer import RabbitMQConsumer

# Configuración de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Punto de entrada del Payment Service"""
    logger.info("Iniciando Payment Service...")

    # Obtener configuración centralizada
    rabbitmq_config = get_rabbitmq_config()

    try:
        # Inicializar consumidor de mensajes
        consumer = RabbitMQConsumer(amqp_url=rabbitmq_config.url)
        logger.info("Consumidor RabbitMQ inicializado")

        # Iniciar consumo de mensajes
        logger.info("Iniciando consumo de mensajes...")
        consumer.start_consuming()

    except KeyboardInterrupt:
        logger.info("Servicio detenido por el usuario")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error crítico en Payment Service: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
