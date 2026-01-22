from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from pathlib import Path
import uvicorn

# Imports Hexagonales
# from ..adapters.http_adapters import HttpOrderAdapter, HttpHealthAdapter
from src.infrastructure.adapters.http_adapters import HttpOrderAdapter, HttpHealthAdapter

app = FastAPI(title="Demo Portal")

# Configuración de Templates
# Template path fix: 'web/templates' is not relative to main.py anymore if we moved main.py
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "web_templates"))

# Inicialización de Adaptadores (Inyección de Dependencias Simple)
order_adapter = HttpOrderAdapter()
health_adapter = HttpHealthAdapter()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Vista principal: Dashboard completo"""
    # 1. Obtener Salud del Sistema
    system_health = health_adapter.check_health()
    
    # 2. Obtener Lista de Pedidos (Simulado o Real)
    orders = order_adapter.get_orders()
    
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "health": system_health, 
            "orders": orders
        }
    )

@app.post("/create-demo-order")
async def create_demo_order(request: Request):
    """Acción: Crea un pedido hardcodeado para demostración"""
    try:
        # Datos de prueba para el flujo
        sample_items = [
            {"product_id": "prod-001", "quantity": 1, "price": 50.0},
            {"product_id": "prod-002", "quantity": 2, "price": 25.0}
        ]
        
        order_id = order_adapter.create_demo_order("customer-demo", sample_items)
        message = f"Pedido creado exitosamente: {order_id}"
    except Exception as e:
        message = f"Error al crear pedido: {str(e)}"

    # Renderizamos de nuevo el dashboard con el mensaje flash
    # Nota: En una app real usaríamos sesiones para flash messages y redirect
    system_health = health_adapter.check_health()
    orders = order_adapter.get_orders()
    
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "health": system_health, 
            "orders": orders,
            "message": message
        }
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
