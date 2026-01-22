"""
Módulo de configuración centralizada para todos los microservicios.
Implementa el patrón de configuración por entorno para arquitectura hexagonal.
"""
import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class DatabaseConfig:
    """Configuración de base de datos"""
    host: str
    port: int
    user: str
    password: str
    name: str
    
    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


@dataclass(frozen=True)
class RabbitMQConfig:
    """Configuración de RabbitMQ"""
    host: str
    port: int
    user: str
    password: str
    
    @property
    def url(self) -> str:
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}/%2f"


@dataclass(frozen=True)
class SecurityConfig:
    """Configuración de seguridad"""
    jwt_secret: str
    jwt_algorithm: str


@dataclass(frozen=True)
class ServiceConfig:
    """Configuración completa de un servicio"""
    database: DatabaseConfig
    rabbitmq: RabbitMQConfig
    security: SecurityConfig
    service_name: str
    service_port: int


@lru_cache(maxsize=1)
def get_database_config(db_name: str = None) -> DatabaseConfig:
    """Obtiene la configuración de base de datos desde variables de entorno"""
    return DatabaseConfig(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        user=os.getenv("DB_USER", "user"),
        password=os.getenv("DB_PASSWORD", "password"),
        name=db_name or os.getenv("DB_NAME", "integrahub_db")
    )


@lru_cache(maxsize=1)
def get_rabbitmq_config() -> RabbitMQConfig:
    """Obtiene la configuración de RabbitMQ desde variables de entorno"""
    return RabbitMQConfig(
        host=os.getenv("RABBITMQ_HOST", "localhost"),
        port=int(os.getenv("RABBITMQ_PORT", "5672")),
        user=os.getenv("RABBITMQ_USER", "user"),
        password=os.getenv("RABBITMQ_PASSWORD", "password")
    )


@lru_cache(maxsize=1)
def get_security_config() -> SecurityConfig:
    """Obtiene la configuración de seguridad desde variables de entorno"""
    return SecurityConfig(
        jwt_secret=os.getenv("JWT_SECRET", "supersecretkey"),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256")
    )


def get_service_config(service_name: str, default_port: int = 8000, db_name: str = None) -> ServiceConfig:
    """Obtiene la configuración completa para un servicio"""
    return ServiceConfig(
        database=get_database_config(db_name),
        rabbitmq=get_rabbitmq_config(),
        security=get_security_config(),
        service_name=service_name,
        service_port=int(os.getenv(f"{service_name.upper()}_PORT", str(default_port)))
    )
