"""Legacy Ingestion Service - Infrastructure Layer Entry Point"""
import logging
import os
import sys

from shared.infrastructure.config import get_service_config
from .adapters.postgres_repository import PostgresInventoryRepository
from .adapters.file_monitor import FileMonitorAdapter
from ..application.services import IngestFileUseCase

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ruta por defecto para el inbox
DEFAULT_INBOX_PATH = "/app/data"


def main():
    """Punto de entrada del Legacy Ingestion Service"""
    logger.info("Iniciando Legacy Ingestion Service...")
    
    # Obtener configuración centralizada
    config = get_service_config("legacy_ingestion_service")
    inbox_path = os.getenv("DATA_INBOX_PATH", DEFAULT_INBOX_PATH)
    
    try:
        # 1. Inicializar repositorio
        repository = PostgresInventoryRepository(config.database.url)
        logger.info("Repositorio PostgreSQL inicializado")
        
        # 2. Inicializar caso de uso
        use_case = IngestFileUseCase(repository)
        logger.info("Caso de uso inicializado")

        # 3. Asegurar que el directorio existe
        if not os.path.exists(inbox_path):
            os.makedirs(inbox_path)
            logger.info(f"Directorio de inbox creado: {inbox_path}")

        # 4. Inicializar y arrancar monitor de archivos
        monitor = FileMonitorAdapter(inbox_path, use_case)
        logger.info(f"Iniciando monitoreo de directorio: {inbox_path}")
        monitor.start()
        
    except KeyboardInterrupt:
        logger.info("Servicio detenido por el usuario")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error crítico en Legacy Ingestion Service: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
