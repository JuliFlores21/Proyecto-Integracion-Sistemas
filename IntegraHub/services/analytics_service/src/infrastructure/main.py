import os
import uvicorn
import time
from .adapters.postgres_repository import PostgresMetricsRepository
from .adapters.stream_consumer import AnalyticsStreamProcessor
from .http.api import create_app
import sys
import os

# Fix path for absolute imports
sys.path.append(os.getcwd())

from src.application.services import ProcessEventUseCase, GetMetricsUseCase

def main():
    print("Starting Analytics Service...")
    
    # Config
    DB_HOST = os.getenv("DB_HOST", "localhost")
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
    DATABASE_URL = f"postgresql://user:password@{DB_HOST}:5432/integrahub_db"
    AMQP_URL = f"amqp://user:password@{RABBITMQ_HOST}:5672/%2f"

    # Wait for DB
    time.sleep(10)

    # 1. Infrastructure / Adapters
    repo = PostgresMetricsRepository(DATABASE_URL)
    
    # 2. Use Cases
    process_use_case = ProcessEventUseCase(repo)
    get_metrics_use_case = GetMetricsUseCase(repo)

    # 3. Start Stream Consumer (Background Thread)
    stream_processor = AnalyticsStreamProcessor(AMQP_URL, process_use_case)
    stream_processor.start()

    # 4. Start HTTP API (Blocking)
    app = create_app(get_metrics_use_case)
    uvicorn.run(app, host="0.0.0.0", port=8004)

if __name__ == "__main__":
    main()
