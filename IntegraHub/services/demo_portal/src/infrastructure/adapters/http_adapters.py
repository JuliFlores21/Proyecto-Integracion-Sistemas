import os
import secrets
import jwt
import datetime
import httpx
from typing import List, Dict
from shared.infrastructure.http_client import BaseHttpClient
from ...application.ports import OrderServicePort, SystemStatusPort
from ...domain.models import DemoOrder, SystemHealth

class HttpOrderAdapter(BaseHttpClient, OrderServicePort):
    def __init__(self):
        url = os.getenv("ORDER_SERVICE_URL", "http://order-service:8000")
        super().__init__(url)

    def create_demo_order(self, customer_id: str, items: List[Dict]) -> str:
        # Generate Valid JWT Token for Internal Communication
        token_payload = {
            "sub": "demo-portal",
            "role": "admin",
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
        }
        token = jwt.encode(token_payload, "supersecretkey", algorithm="HS256") # Shared secret matches security.py

        headers = {
            "X-Idempotency-Key": secrets.token_hex(8),
            "Authorization": f"Bearer {token}"
        }
        payload = {"customer_id": customer_id, "items": items}
        
        response = self._post("orders", payload, headers)
        return response["order_id"]

    def get_orders(self) -> List[DemoOrder]:
        try:
            # Call the real endpoint
            # Note: _get() in BaseHttpClient currently doesn't support headers, 
            # but the GET /orders currently doesn't enforce Auth (it should, but for demo it's open).
            orders_data = self._get("orders")
            
            if not orders_data:
                return []
                
            return [
                DemoOrder(
                    order_id=str(o.get("order_id")),
                    status=str(o.get("status")),
                    total=float(o.get("total_amount", 0.0)),
                    correlation_id="N/A" # Not returned by simple API yet
                )
                for o in orders_data
            ]
        except Exception:
            # Fallback to empty list or logs
            return []

class HttpHealthAdapter(SystemStatusPort):
    def check_health(self) -> List[SystemHealth]:
        # HTTP Services
        http_services = {
            "Order Service": os.getenv("ORDER_SERVICE_URL", "http://order-service:8000"),
            "Analytics Service": "http://analytics-service:8004"
        }
        
        # Worker Services (Checked via RabbitMQ Management API)
        worker_services = {
            "Inventory": "inventory_queue",
            "Payment": "payment_queue",
            "Notification": "notification_queue"
        }
        
        results = []
        
        # 1. Check HTTP Services
        for name, url in http_services.items():
            try:
                resp = httpx.get(f"{url}/docs", timeout=2.0)
                status = "UP" if resp.status_code == 200 else "WARN"
            except Exception:
                status = "DOWN"
            results.append(SystemHealth(name, status, url))

        # 2. Check Worker Services (via RabbitMQ)
        rabbit_mgmt_url = "http://rabbitmq:15672/api/queues/%2F"
        rabbit_auth = ("user", "password") # Default from docker-compose
        
        for name, queue in worker_services.items():
            try:
                resp = httpx.get(f"{rabbit_mgmt_url}/{queue}", auth=rabbit_auth, timeout=2.0)
                if resp.status_code == 200:
                    data = resp.json()
                    consumers = data.get("consumers", 0)
                    status = "UP" if consumers > 0 else "WARN (No Consumers)"
                else:
                    status = "DOWN (Queue not found)"
            except Exception as e:
                status = f"DOWN (Mgmt API Error)"
            
            results.append(SystemHealth(name, status, f"Queue: {queue}"))

        return results
