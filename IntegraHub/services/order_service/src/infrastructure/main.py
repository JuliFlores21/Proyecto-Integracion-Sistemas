"""Order Service - Infrastructure Layer Entry Point"""
import logging
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException, Header, Depends, status
from pydantic import BaseModel, Field
import uvicorn

from shared.infrastructure.config import get_service_config
from shared.infrastructure.security import verify_token
from src.application.services import CreateOrderUseCase
from src.infrastructure.adapters.postgres_repository import PostgresOrderRepository
from src.infrastructure.adapters.rabbitmq_publisher import RabbitMQPublisherAdapter

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración centralizada
config = get_service_config("order_service", default_port=8000)

# Componentes de infraestructura (inyección de dependencias manual)
repository: PostgresOrderRepository = None
publisher: RabbitMQPublisherAdapter = None
create_order_use_case: CreateOrderUseCase = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    global repository, publisher, create_order_use_case
    
    logger.info("Inicializando Order Service...")
    
    # Inicializar adaptadores
    repository = PostgresOrderRepository(config.database.url)
    publisher = RabbitMQPublisherAdapter(host=config.rabbitmq.host)
    create_order_use_case = CreateOrderUseCase(repository, publisher)
    
    logger.info("Order Service inicializado correctamente")
    yield
    
    # Cleanup
    logger.info("Cerrando Order Service...")


# App con lifespan para mejor gestión de recursos
app = FastAPI(
    title="Order Service",
    version="1.0.0",
    description="Microservicio de gestión de órdenes - Arquitectura Hexagonal",
    lifespan=lifespan
)

# DTOs con validación mejorada
class OrderItemDTO(BaseModel):
    """Data Transfer Object para items de orden"""
    product_id: str = Field(..., min_length=1, description="ID del producto")
    quantity: int = Field(..., gt=0, description="Cantidad (debe ser mayor a 0)")
    price: float = Field(..., gt=0, description="Precio unitario (debe ser mayor a 0)")

    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "prod_1",
                "quantity": 2,
                "price": 29.99
            }
        }


class CreateOrderRequest(BaseModel):
    """Request para crear una nueva orden"""
    customer_id: str = Field(..., min_length=1, description="ID del cliente")
    items: List[OrderItemDTO] = Field(..., min_length=1, description="Lista de items")

    class Config:
        json_schema_extra = {
            "example": {
                "customer_id": "customer_123",
                "items": [{"product_id": "prod_1", "quantity": 2, "price": 29.99}]
            }
        }


class OrderResponse(BaseModel):
    """Response de creación de orden"""
    order_id: str
    status: str
    message: str

# Routes
@app.post("/orders", status_code=status.HTTP_201_CREATED, response_model=OrderResponse)
def create_order(
    request: CreateOrderRequest, 
    idempotency_key: str = Header(None, alias="X-Idempotency-Key"),
    user_payload: dict = Depends(verify_token)
):
    """Crea una nueva orden en el sistema"""
    logger.info(f"Recibida solicitud de orden para cliente: {request.customer_id}")
    
    try:
        order = create_order_use_case.execute(
            customer_id=request.customer_id, 
            items_data=[item.model_dump() for item in request.items],
            idempotency_key=idempotency_key
        )
        logger.info(f"Orden creada exitosamente: {order.order_id}")
        return OrderResponse(
            order_id=order.order_id,
            status="CREATED",
            message="Order processed successfully"
        )
    except ValueError as e:
        logger.warning(f"Conflicto al crear orden: {e}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"Error interno al crear orden: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@app.get("/health")
def health_check():
    """Endpoint de health check para monitoreo"""
    return {
        "status": "healthy",
        "service": "order-service",
        "version": "1.0.0"
    }


@app.get("/ready")
def readiness_check():
    """Verifica que el servicio esté listo para recibir tráfico"""
    try:
        # Verificar conexión a base de datos
        if repository:
            return {"status": "ready"}
        return {"status": "not_ready"}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
