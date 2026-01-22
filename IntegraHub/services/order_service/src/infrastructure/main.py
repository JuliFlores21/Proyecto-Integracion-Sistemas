from fastapi import FastAPI, HTTPException, Header, Depends, status
import uvicorn
from pydantic import BaseModel
from typing import List
import os
from shared.infrastructure.security import verify_token
# Absolute imports to avoid relative hell
from src.application.services import CreateOrderUseCase
from src.infrastructure.adapters.postgres_repository import PostgresOrderRepository
from src.infrastructure.adapters.rabbitmq_publisher import RabbitMQPublisherAdapter
from src.infrastructure.adapters.rabbitmq_consumer import RabbitMQConsumer

# Config
DB_HOST = os.getenv("DB_HOST", "localhost")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
DATABASE_URL = f"postgresql://user:password@{DB_HOST}:5432/integrahub_db"
AMQP_URL = f"amqp://user:password@{RABBITMQ_HOST}:5672/%2f"

# App
app = FastAPI(title="Order Service", version="1.0.0")

# Dependencies (Manual DI for Hexagonal Arch)
repository = PostgresOrderRepository(DATABASE_URL)
publisher = RabbitMQPublisherAdapter(host=RABBITMQ_HOST)
create_order_use_case = CreateOrderUseCase(repository, publisher)

# Background Consumer
consumer = RabbitMQConsumer(AMQP_URL, repository)

@app.on_event("startup")
def startup_event():
    consumer.start_in_background()

@app.on_event("shutdown")
def shutdown_event():
    consumer.stop()

# DTOs

# DTOs
class OrderItemDTO(BaseModel):
    product_id: str
    quantity: int
    price: float

class CreateOrderRequest(BaseModel):
    customer_id: str
    items: List[OrderItemDTO]

# Routes
@app.post("/orders", status_code=201)
def create_order(
    request: CreateOrderRequest, 
    idempotency_key: str = Header(None, alias="X-Idempotency-Key"),
    user_payload: dict = Depends(verify_token)
):
    try:
        # Pass DTO data to application layer
        order = create_order_use_case.execute(
            customer_id=request.customer_id, 
            items_data=[item.dict() for item in request.items],
            idempotency_key=idempotency_key
        )
        return {"order_id": order.order_id, "status": "CREATED", "message": "Order processed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/orders", response_model=List[dict])
def get_orders():
    try:
        orders = repository.get_all()
        return [
            {
                "order_id": o.order_id,
                "customer_id": o.customer_id,
                "status": o.status,
                "total_amount": o.total_amount,
                "created_at": o.created_at,
                "items": [i.product_id for i in o.items]
            }
            for o in orders
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
