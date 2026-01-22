"""Analytics Service - Infrastructure Layer Entry Point"""
import logging
import sys

import uvicorn

from shared.infrastructure.config import get_service_config
from src.application.services import ProcessEventUseCase, GetMetricsUseCase
from .adapters.postgres_repository import PostgresMetricsRepository
from .adapters.stream_consumer import AnalyticsStreamProcessor
from .http.api import create_app

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Punto de entrada del Analytics Service"""
    logger.info("Iniciando Analytics Service...")
    
    # Obtener configuración centralizada
    config = get_service_config(
        "analytics_service",
        default_port=8004,
        db_name="integrahub_analytics"
    )
    
    try:
        # 1. Inicializar repositorio
        repo = PostgresMetricsRepository(config.database.url)
        logger.info("Repositorio PostgreSQL inicializado")
        
        # 2. Inicializar casos de uso
        process_use_case = ProcessEventUseCase(repo)
        get_metrics_use_case = GetMetricsUseCase(repo)
        logger.info("Casos de uso inicializados")

        # 3. Iniciar procesador de stream (hilo en segundo plano)
        stream_processor = AnalyticsStreamProcessor(
            config.rabbitmq.url,
            process_use_case
        )
        stream_processor.start()
        logger.info("Procesador de stream iniciado")

        # 4. Iniciar API HTTP (bloqueante)
        app = create_app(get_metrics_use_case)
        logger.info(f"Iniciando API HTTP en puerto {config.service_port}")
        uvicorn.run(app, host="0.0.0.0", port=config.service_port)
        
    except KeyboardInterrupt:
        logger.info("Servicio detenido por el usuario")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error crítico en Analytics Service: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
