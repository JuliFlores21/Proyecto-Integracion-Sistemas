import os
import time
from .adapters.rabbitmq_consumer import RabbitMQConsumer

def main():
    print("Starting Payment Service...")
    
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
    AMQP_URL = f"amqp://user:password@{RABBITMQ_HOST}:5672/%2f"

    # Simple wait for RabbitMQ
    time.sleep(10)
    
    consumer = RabbitMQConsumer(amqp_url=AMQP_URL)
    
    try:
        consumer.start_consuming()
    except KeyboardInterrupt:
        print("Stopping...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
