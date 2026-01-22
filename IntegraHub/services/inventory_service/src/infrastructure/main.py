"""Inventory Service - Infrastructure Layer Entry Point"""

import logging
import sys

from shared.infrastructure.config import get_service_config
from .adapters.postgres_repository import PostgresInventoryRepository
from .adapters.rabbitmq_consumer import RabbitMQConsumer

# Configuración de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Punto de entrada del Inventory Service"""
    logger.info("Iniciando Inventory Service...")

    # Obtener configuración centralizada
    config = get_service_config("inventory_service")

    try:
        # Inicializar repositorio
        repository = PostgresInventoryRepository(config.database.url)
        logger.info("Repositorio PostgreSQL inicializado")

        # Inicializar consumidor de mensajes
        consumer = RabbitMQConsumer(amqp_url=config.rabbitmq.url, repository=repository)
        logger.info("Consumidor RabbitMQ inicializado")

        # Iniciar consumo de mensajes
        logger.info("Iniciando consumo de mensajes...")
        consumer.start_consuming()

    except KeyboardInterrupt:
        logger.info("Servicio detenido por el usuario")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error crítico en Inventory Service: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
