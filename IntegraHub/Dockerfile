# Dockerfile optimizado para microservicios con arquitectura hexagonal
FROM python:3.11-slim as base

# Etapa base con dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip

WORKDIR /app

# Argumentos de build
ARG SERVICE_NAME
ENV SERVICE_NAME=${SERVICE_NAME}

# Configuración de Python
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copiar y instalar dependencias
COPY services/${SERVICE_NAME}/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código compartido y del servicio
COPY shared/ ./shared/
COPY services/${SERVICE_NAME}/src/ ./src/

# Usuario no-root para seguridad
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check genérico
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Comando por defecto
CMD ["python", "-m", "src.infrastructure.main"]
