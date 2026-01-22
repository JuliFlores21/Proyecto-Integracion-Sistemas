FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

# Ensure directory exists
RUN mkdir -p /app/data

CMD ["python", "-m", "src.infrastructure.main"]
