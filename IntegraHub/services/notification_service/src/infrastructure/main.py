import os
import time
from .adapters.notification_channels import SlackAdapter, EmailAdapter
from .adapters.rabbitmq_consumer import RabbitMQConsumer
from ..application.services import NotificationUseCase

def main():
    print("Starting Notification Service...")
    
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")

    # Nota: esta URL usa user:password de forma fija.
    # Por eso `.env.example` define RABBITMQ_USER=user y RABBITMQ_PASSWORD=password,
    # para mantener consistencia con los contenedores.
    AMQP_URL = f"amqp://user:password@{RABBITMQ_HOST}:5672/%2f"

    time.sleep(10) # Wait for RabbitMQ

    # 1. Initialize Adapters
    slack_channel = SlackAdapter()
    email_channel = EmailAdapter()

    # 2. Initialize Use Case with list of channels (Pub/Sub Fanout)
    use_case = NotificationUseCase(channels=[slack_channel, email_channel])

    # 3. Initialize Consumer
    consumer = RabbitMQConsumer(amqp_url=AMQP_URL, use_case=use_case)

    try:
        consumer.start_consuming()
    except KeyboardInterrupt:
        print("Stopping...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
