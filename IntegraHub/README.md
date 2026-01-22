# IntegraHub

Proyecto de integración de sistemas basado en Arquitectura Hexagonal y Microservicios.

## Estructura del Proyecto

El proyecto sigue una estructura de monorepo con servicios independientes, cada uno implementando Arquitectura Hexagonal (Ports and Adapters).

```
IntegraHub/
├── docker-compose.yml          # Orquestación de contenedores
├── data/                       # Volúmenes locales (ej. CSVs)
├── services/
│   ├── order_service/          # Flujo A: API -> Eventos
│   │   ├── src/
│   │   │   ├── application/    # Casos de uso, Puertos (Interfaces)
│   │   │   ├── domain/         # Entidades, Reglas de negocio
│   │   │   ├── infrastructure/ # Adaptadores (FastAPI, RabbitMQ, SQL)
│   │   │   └── main.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── inventory_service/      # Flujo A: Consumidor de eventos
│   ├── payment_service/        # Flujo A: Proceso de pagos
│   ├── notification_service/   # Flujo B: Notificaciones Pub/Sub
│   ├── legacy_ingestion_service/ # Flujo C: Ingesta Legacy (CSV)
│   └── analytics_service/      # Flujo D: Analytics (Kafka/Batch)
└── shared/                     # Código compartido (si aplica)
```

## Requisitos Previos

- Docker
- Docker Compose

## Ejecución

Para levantar toda la infraestructura y servicios:

```bash
docker-compose up --build -d
```
