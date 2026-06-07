# ── Publisher image ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS base

LABEL maintainer="amithalbreich15@gmail.com"
LABEL description="RabbitMQ Publisher – DevOps Assignment Task 1"

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY publisher.py .
COPY consumer.py .

# Default: run publisher; override CMD to run consumer
CMD ["python", "publisher.py"]
