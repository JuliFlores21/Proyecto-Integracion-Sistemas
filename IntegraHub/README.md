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

1.  **Git**: Para clonar el repositorio.
2.  **Docker Desktop**: Debe estar instalado y ejecutándose.
3.  **Terminal**: PowerShell (recomendado en Windows) o Bash.

## Guía Paso a Paso (Ejecución Desde Cero)

### 1. Clonar el Repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd Proyecto-Integracion-Sistemas/IntegraHub
```

_(Asegúrate de estar dentro de la carpeta `IntegraHub` donde se encuentra el `docker-compose.yml`)_

### 2. Ejecutar el Proyecto

Tienes dos opciones para iniciar el sistema:

#### Opción A: Script Automático (Recomendado en Windows)

Ejecuta el script de despliegue que configurará el entorno y levantará los servicios:

```powershell
./deploy.ps1
```

#### Opción B: Manualmente

Si prefieres hacerlo paso a paso o estás en otro sistema operativo:

1.  **Configurar Variables de Entorno**:
    Crea el archivo `.env` copiando el ejemplo (si no existe):

    ```bash
    cp .env.example .env
    # En Windows CMD: copy .env.example .env
    ```

2.  **Crear Carpetas de Datos**:
    Asegúrate de que existan los directorios necesarios:

    ```bash
    mkdir -p data/inbox
    mkdir -p data/postgres
    ```

3.  **Levantar Contenedores**:
    ```bash
    docker-compose up --build -d
    ```

### 3. Verificar la Instalación

Una vez que los contenedores estén corriendo, puedes acceder a los siguientes servicios:

- **API Pedidos (Swagger/Docs)**: [http://localhost:8001/docs](http://localhost:8001/docs)
- **Demo Portal (Frontend)**: [http://localhost:8088/](http://localhost:8088/)
- **API Métricas**: [http://localhost:8004/metrics](http://localhost:8004/metrics)
- **RabbitMQ Management**: [http://localhost:15672](http://localhost:15672) (Usuario/Pass: `guest` / `guest` por defecto)

Para detener los servicios:

```bash
docker-compose down
```
