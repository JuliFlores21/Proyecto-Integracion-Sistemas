import os
import time
from .adapters.postgres_repository import PostgresInventoryRepository
from .adapters.file_monitor import FileMonitorAdapter
from ..application.services import IngestFileUseCase

def main():
    print("Starting Legacy Ingestion Service...")
    
    # Config
    DB_HOST = os.getenv("DB_HOST", "localhost")
    # Using the same DB as Inventory Service
    DATABASE_URL = f"postgresql://user:password@{DB_HOST}:5432/integrahub_db"
    INBOX_PATH = "/app/data" # Local Docker volume path

    # Wait for DB
    time.sleep(10)

    # 1. Adapter - Repository
    repository = PostgresInventoryRepository(DATABASE_URL)
    
    # 2. Use Case
    use_case = IngestFileUseCase(repository)

    # 3. Adapter - File System Monitor
    # Ensure directory exists
    if not os.path.exists(INBOX_PATH):
        os.makedirs(INBOX_PATH)

    monitor = FileMonitorAdapter(INBOX_PATH, use_case)
    monitor.start()

if __name__ == "__main__":
    main()
