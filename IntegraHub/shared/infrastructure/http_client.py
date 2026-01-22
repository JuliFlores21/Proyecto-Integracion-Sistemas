from typing import Optional, Dict
import httpx
from abc import ABC, abstractmethod

class BaseHttpClient(ABC):
    """
    Cliente HTTP Base para consumir microservicios internos.
    Ubicado en shared/ para cumplimiento de restricción de arquitectura.
    """
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.Client(timeout=5.0)

    def _get(self, endpoint: str):
        try:
            response = self.client.get(f"{self.base_url}/{endpoint.lstrip('/')}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            return None  # Fail safe para Demo

    def _post(self, endpoint: str, data: Dict, headers: Optional[Dict] = None):
        try:
            response = self.client.post(
                f"{self.base_url}/{endpoint.lstrip('/')}", 
                json=data,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise e
