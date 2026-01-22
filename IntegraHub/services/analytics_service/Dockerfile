FROM python:3.9-slim

WORKDIR /app

# Install dependencies needed for confluent-kafka (C library)
RUN apt-get update && apt-get install -y gcc librdkafka-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

CMD ["python", "-m", "src.infrastructure.main"]
