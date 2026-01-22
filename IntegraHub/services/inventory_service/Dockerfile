FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Wait script or similar might be useful, but for now just copy src
COPY src/ ./src/

CMD ["python", "-m", "src.infrastructure.main"]
