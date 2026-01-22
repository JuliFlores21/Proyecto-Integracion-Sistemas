FROM python:3.9-slim

WORKDIR /app

# Arguments
ARG SERVICE_NAME

# 1. Shared Environment Setup
ENV PYTHONPATH=/app

# 2. Install dependencies
# Copy specific service requirements
COPY services/${SERVICE_NAME}/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy Code
# Copy shared library
COPY shared/ ./shared/
# Copy service code -> mapped to /app/src
COPY services/${SERVICE_NAME}/src/ ./src/

# Default Command (Can be overridden in compose)
CMD ["python", "-m", "src.infrastructure.main"]
