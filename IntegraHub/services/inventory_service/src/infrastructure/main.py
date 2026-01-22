import os
import time
from .adapters.postgres_repository import PostgresInventoryRepository
from .adapters.rabbitmq_consumer import RabbitMQConsumer

def main():
    print("Starting Inventory Service...")
    
    # Config
    DB_HOST = os.getenv("DB_HOST", "localhost")
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
    DATABASE_URL = f"postgresql://user:password@{DB_HOST}:5432/integrahub_db"
    AMQP_URL = f"amqp://user:password@{RABBITMQ_HOST}:5672/%2f"

    # Infrastructure Setup
    # Wait for DB to be ready (Primitive wait, in prod use healthchecks/wait-for-it)
    time.sleep(5) 
    
    repository = PostgresInventoryRepository(DATABASE_URL)
    
    consumer = RabbitMQConsumer(amqp_url=AMQP_URL, repository=repository)
    
    try:
        consumer.start_consuming()
    except KeyboardInterrupt:
        print("Stopping...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
