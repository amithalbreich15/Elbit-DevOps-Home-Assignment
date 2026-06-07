# ── CPU Monitor image ────────────────────────────────────────────────────────
FROM python:3.12-slim

LABEL maintainer="amithalbreich15@gmail.com"
LABEL description="CPU Usage Monitor – DevOps Assignment Task 2"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY cpu_monitor.py .

# Expose Prometheus metrics port (only used if METRICS_ENABLED=true)
EXPOSE 8000

# Environment variable defaults (override via docker run -e or docker-compose)
ENV CPU_THRESHOLD=80 \
    CHECK_INTERVAL=5 \
    LOG_FILE="" \
    METRICS_ENABLED=false \
    METRICS_PORT=8000

CMD ["python", "cpu_monitor.py"]
