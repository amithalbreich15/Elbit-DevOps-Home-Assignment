# DevOps Home Assignment – Elbit Systems
**Author:** Amit Halbreich | amithalbreich15@gmail.com  
**GitHub:** https://github.com/amithalbreich15/Elbit-DevOps-Home-Assignment

---

## Repository Structure

```
elbit-devops-home-assignment/
├── task1_message_queue/
│   ├── publisher.py          # RabbitMQ publisher
│   ├── consumer.py           # RabbitMQ consumer with DLQ & graceful shutdown
│   ├── docker-compose.yml    # RabbitMQ broker (with health-check)
│   ├── rabbitmq.conf         # Broker configuration
│   ├── Dockerfile            # Container image for both scripts
│   └── requirements.txt
├── task2_cpu_monitor/
│   ├── cpu_monitor.py        # CPU monitoring service
│   ├── cpu_monitor.service   # systemd unit file (production deploy)
│   ├── Dockerfile
│   └── requirements.txt
├── task3_multicast/
│   └── multicast_explanation.md
├── .github/
│   └── workflows/
│       └── ci.yml            # GitHub Actions CI pipeline
└── README.md
```

---

## Prerequisites

| Tool | Min version | Install |
|------|-------------|---------|
| Python | 3.10+ | https://python.org |
| Docker + Docker Compose v2 | Latest | https://docs.docker.com/get-docker/ |
| pip | 22+ | bundled with Python |

---

## Task 1 — RabbitMQ Publisher & Consumer

### Quick Start (local)

```bash
cd task1_message_queue

# 1. Start RabbitMQ
docker compose up -d
#    Wait until healthy: docker compose ps

# 2. Install Python deps
pip install -r requirements.txt

# 3. Start consumer (Terminal 1)
python consumer.py

# 4. Run publisher (Terminal 2)
python publisher.py
```

Management UI → http://localhost:15672  (guest / guest)

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RABBITMQ_HOST` | `localhost` | Broker hostname |
| `RABBITMQ_PORT` | `5672` | AMQP port |
| `RABBITMQ_USER` | `guest` | Username |
| `RABBITMQ_PASS` | `guest` | Password |
| `QUEUE_NAME` | `ABC` | Queue name |
| `NUM_MESSAGES` | `10` | Messages to send (publisher) |
| `MESSAGE_DELAY` | `0.5` | Seconds between messages |
| `MAX_RETRIES` | `5` | Connection retry attempts |

### Run with Docker

```bash
# Publisher
docker build -t devops-publisher task1_message_queue/
docker run --network host \
  -e RABBITMQ_HOST=localhost \
  -e NUM_MESSAGES=10 \
  devops-publisher

# Consumer
docker run --network host \
  -e RABBITMQ_HOST=localhost \
  devops-publisher python consumer.py
```

### Stop RabbitMQ

```bash
docker compose down          # keep volume
docker compose down -v       # remove volume too
```

---

## Task 2 — CPU Monitor Service

### Run Locally

```bash
pip install -r task2_cpu_monitor/requirements.txt

# With defaults (threshold 80%, check every 5s)
python task2_cpu_monitor/cpu_monitor.py

# Custom threshold and interval
CPU_THRESHOLD=60 CHECK_INTERVAL=3 python task2_cpu_monitor/cpu_monitor.py
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CPU_THRESHOLD` | `80.0` | Alert threshold (%) |
| `CHECK_INTERVAL` | `5` | Seconds between checks |
| `LOG_FILE` | `cpu_monitor.log` | Log file path (empty = stdout only) |
| `SMTP_HOST` | `` | SMTP server (leave blank to disable email) |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_USER` | `` | SMTP username |
| `SMTP_PASS` | `` | SMTP password |
| `ALERT_FROM` | `` | Sender email |
| `ALERT_TO` | `` | Recipient email |
| `METRICS_ENABLED` | `false` | Enable Prometheus `/metrics` endpoint |
| `METRICS_PORT` | `8000` | Prometheus port |

### Deploy as systemd Service (Linux)

```bash
sudo cp task2_cpu_monitor/cpu_monitor.py /opt/cpu_monitor/
sudo pip3 install psutil

sudo cp task2_cpu_monitor/cpu_monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now cpu_monitor

# Check status
sudo systemctl status cpu_monitor

# Follow logs
sudo journalctl -u cpu_monitor -f
```

### Run with Docker

```bash
docker build -t devops-cpu-monitor task2_cpu_monitor/
docker run \
  -e CPU_THRESHOLD=80 \
  -e CHECK_INTERVAL=5 \
  devops-cpu-monitor
```

---

## Task 3 (Bonus) — Multicast

See `task3_multicast/multicast_explanation.md` for a full explanation covering:
- Definition and use cases
- PIM-SM, GRE tunneling, AMT, mVPN
- Concrete bandwidth-saving scenario

---

## CI / CD

A GitHub Actions pipeline (`.github/workflows/ci.yml`) runs automatically on every push:

1. Lints all Python files with `pylint`
2. Smoke-tests the publisher against a live RabbitMQ container
3. Smoke-tests the CPU monitor (3-second run)
4. Builds Docker images for both tasks

---

## Push to GitHub

```bash
git init
git add .
git commit -m "Initial Commit Elbit-DevOps-Home-Assignment solution"
git remote add origin https://github.com/amithalbreich15/Elbit-DevOps-Home-Assignment.git
git push -u origin main
```
