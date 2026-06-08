# DevOps Home Assignment – Elbit Systems

**Author:** Amit Halbreich  
**GitHub:** https://github.com/amithalbreich15/Elbit-DevOps-Home-Assignment

---

## Overview

This repository contains a complete DevOps-oriented solution for the Elbit Systems home assignment.

The assignment includes three main parts:

1. **Python Publisher and Consumer using a Message Queue**
2. **CPU Usage Monitoring Service with Alerts**
3. **Bonus: Multicast Networking Explanation**

The project goes beyond the basic requirements by adding production-style DevOps features such as:

- Docker and Docker Compose
- RabbitMQ management UI
- Durable queues and persistent messages
- Manual message acknowledgments
- Dead-letter queue handling
- CPU monitoring with configurable thresholds
- SMTP email alert support
- Docker secrets support
- Prometheus metrics endpoint
- Grafana dashboard support
- Linux `systemd` service file
- GitHub Actions CI pipeline

---

## Repository Structure

```text
Elbit-DevOps-Home-Assignment/
├── task1_message_queue/
│   ├── publisher.py
│   ├── consumer.py
│   ├── docker-compose.yml
│   ├── rabbitmq.conf
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
│
├── task2_cpu_monitor/
│   ├── cpu_monitor.py
│   ├── cpu_monitor.service
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── Dockerfile.linux
│   ├── Dockerfile.windows
│   ├── requirements.txt
│   ├── prometheus/
│   ├── grafana/
│   ├── stress_client/
│   └── secrets/
│
├── task3_multicast/
│   └── multicast_explanation.md
│
├── docs/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── .gitignore
└── README.md
```

---

## Prerequisites

Before running the project, make sure you have:

| Tool | Version |
|------|---------|
| Python | 3.10+ |
| Docker | Latest stable version |
| Docker Compose | v2+ |
| pip | 22+ |

Optional:

| Tool | Purpose |
|------|---------|
| systemd | Run CPU monitor as a Linux service |
| Prometheus | Collect CPU monitor metrics |
| Grafana | Visualize CPU usage and alerts |

---

# Task 1 — RabbitMQ Publisher and Consumer

## Description

This task implements a simple message queue system using **RabbitMQ** and Python.

The system contains:

- A **publisher** that sends messages to a RabbitMQ queue named `ABC`
- A **consumer** that subscribes to the same queue and prints/processes received messages

RabbitMQ was chosen because it is lightweight, reliable, easy to run with Docker, and suitable for classic producer-consumer workloads.

---

## Features

- Python publisher and consumer
- Queue name configurable by environment variable
- Default queue: `ABC`
- Durable RabbitMQ queue
- Persistent messages
- Manual acknowledgments
- Dead-letter queue support
- Retry logic for RabbitMQ connection
- Graceful shutdown for the consumer
- Docker Compose setup for RabbitMQ
- RabbitMQ Management UI

---

## Task 1 Files

```text
task1_message_queue/
├── publisher.py          # Sends messages to RabbitMQ
├── consumer.py           # Consumes messages from RabbitMQ
├── docker-compose.yml    # Runs RabbitMQ locally
├── rabbitmq.conf         # RabbitMQ configuration
├── Dockerfile            # Container image for publisher/consumer
├── requirements.txt      # Python dependencies
└── .env.example          # Example environment variables
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RABBITMQ_HOST` | `localhost` | RabbitMQ hostname |
| `RABBITMQ_PORT` | `5672` | RabbitMQ AMQP port |
| `RABBITMQ_USER` | `guest` | RabbitMQ username |
| `RABBITMQ_PASS` | `guest` | RabbitMQ password |
| `QUEUE_NAME` | `ABC` | Queue name |
| `DLQ_NAME` | `ABC.dlq` | Dead-letter queue name |
| `NUM_MESSAGES` | `10` | Number of messages sent by publisher |
| `MESSAGE_DELAY` | `0.5` | Delay between messages |
| `MAX_RETRIES` | `5` | RabbitMQ connection retry attempts |

---

## Run Task 1 Locally

### 1. Start RabbitMQ

```bash
cd task1_message_queue
docker compose up -d
```

Check that RabbitMQ is running:

```bash
docker compose ps
```

RabbitMQ Management UI:

```text
http://localhost:15672
```

Default credentials:

```text
Username: guest
Password: guest
```

---

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

### 3. Start the Consumer

Open Terminal 1:

```bash
python consumer.py
```

---

### 4. Run the Publisher

Open Terminal 2:

```bash
python publisher.py
```

Expected result:

```text
Publisher sends messages to queue ABC.
Consumer receives and prints the messages.
```

---

## Run Task 1 with Docker

Build the image:

```bash
docker build -t elbit-rabbitmq-client .
```

Run the consumer:

```bash
docker run --rm \
  --network host \
  -e RABBITMQ_HOST=localhost \
  -e QUEUE_NAME=ABC \
  elbit-rabbitmq-client python consumer.py
```

Run the publisher:

```bash
docker run --rm \
  --network host \
  -e RABBITMQ_HOST=localhost \
  -e QUEUE_NAME=ABC \
  -e NUM_MESSAGES=10 \
  elbit-rabbitmq-client python publisher.py
```

---

## Stop RabbitMQ

```bash
docker compose down
```

To remove the RabbitMQ volume as well:

```bash
docker compose down -v
```

---

# Task 2 — CPU Monitoring Service

## Description

This task implements a CPU monitoring service in Python.

The service continuously monitors CPU usage and triggers an alert when CPU usage exceeds a configured threshold.

The assignment requirement was to alert when CPU usage exceeds **80%**. The threshold is configurable, so it can be lowered during testing.

---

## Features

- Continuous CPU monitoring
- Configurable CPU threshold
- Configurable check interval
- Logging to console or file
- SMTP email alerts
- Docker secrets support
- Prometheus `/metrics` endpoint
- Grafana dashboard support
- Docker Compose monitoring stack
- Stress client for testing alerts
- Linux `systemd` service file
- Graceful shutdown handling

---

## Task 2 Files

```text
task2_cpu_monitor/
├── cpu_monitor.py          # Main CPU monitoring service
├── cpu_monitor.service     # systemd service file
├── docker-compose.yml      # Full monitoring stack
├── Dockerfile              # Docker image
├── Dockerfile.linux        # Linux-specific Dockerfile
├── Dockerfile.windows      # Windows-compatible Dockerfile
├── requirements.txt        # Python dependencies
├── prometheus/             # Prometheus config
├── grafana/                # Grafana dashboards/provisioning
├── stress_client/          # CPU stress testing container
└── secrets/                # Local secret placeholders
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CPU_THRESHOLD` | `80.0` | CPU alert threshold percentage |
| `CHECK_INTERVAL` | `5` | Seconds between CPU checks |
| `LOG_FILE` | empty/stdout | Optional log file path |
| `SMTP_HOST` | empty | SMTP server hostname |
| `SMTP_PORT` | `587` | SMTP server port |
| `SMTP_USER` | empty | SMTP username |
| `SMTP_PASS` | empty | SMTP password |
| `ALERT_FROM` | empty | Sender email address |
| `ALERT_TO` | empty | Alert recipient email address |
| `METRICS_ENABLED` | `false` | Enable Prometheus metrics |
| `METRICS_PORT` | `8000` | Metrics server port |

---

## Run Task 2 Locally

Install dependencies:

```bash
pip install -r task2_cpu_monitor/requirements.txt
```

Run with default configuration:

```bash
python task2_cpu_monitor/cpu_monitor.py
```

Run with a custom threshold:

```bash
CPU_THRESHOLD=60 CHECK_INTERVAL=3 python task2_cpu_monitor/cpu_monitor.py
```

On Windows PowerShell:

```powershell
$env:CPU_THRESHOLD="60"
$env:CHECK_INTERVAL="3"
python task2_cpu_monitor/cpu_monitor.py
```

---

## Run Task 2 with Docker

```bash
cd task2_cpu_monitor
docker build -t elbit-cpu-monitor .
```

```bash
docker run --rm \
  -e CPU_THRESHOLD=80 \
  -e CHECK_INTERVAL=5 \
  elbit-cpu-monitor
```

For easier testing, use a lower threshold:

```bash
docker run --rm \
  -e CPU_THRESHOLD=20 \
  -e CHECK_INTERVAL=5 \
  elbit-cpu-monitor
```

---

## Run Full Monitoring Stack

The Docker Compose stack includes:

- CPU monitor
- CPU stress client
- Prometheus
- Grafana

Start the stack:

```bash
cd task2_cpu_monitor
docker compose up -d --build
```

View logs:

```bash
docker compose logs -f cpu-monitor
```

Open the services:

```text
CPU metrics: http://localhost:8000/metrics
Prometheus:  http://localhost:9090
Grafana:     http://localhost:3000
```

Default Grafana credentials are usually:

```text
Username: admin
Password: admin
```

Stop the stack:

```bash
docker compose down
```

Remove volumes too:

```bash
docker compose down -v
```

---

## SMTP Email Alerts

To enable email alerts, configure SMTP settings.

Example for Gmail App Password:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_google_app_password
ALERT_FROM=your_email@gmail.com
ALERT_TO=recipient_email@gmail.com
CPU_THRESHOLD=80
```

Important:

Do not commit real SMTP passwords to GitHub.

Use one of the following instead:

- `.env` file excluded by `.gitignore`
- Docker secrets
- CI/CD secret variables
- Server-side environment variables

---

## Docker Secrets

The CPU monitor supports reading sensitive values from Docker secrets.

Example secret files:

```text
task2_cpu_monitor/secrets/smtp_pass
task2_cpu_monitor/secrets/alert_to
```

Example:

```bash
echo "your_app_password" > secrets/smtp_pass
echo "recipient@example.com" > secrets/alert_to
```

Then run:

```bash
docker compose up -d --build
```

The app reads the secrets from:

```text
/run/secrets/smtp_pass
/run/secrets/alert_to
```

---

## Deploy CPU Monitor as a Linux systemd Service

### 1. Create Application Directory

```bash
sudo mkdir -p /opt/cpu_monitor
sudo cp task2_cpu_monitor/cpu_monitor.py /opt/cpu_monitor/
```

---

### 2. Install Dependencies

```bash
sudo apt update
sudo apt install -y python3 python3-pip
sudo pip3 install psutil prometheus-client
```

---

### 3. Create Environment File

```bash
sudo nano /etc/cpu_monitor.env
```

Example:

```env
CPU_THRESHOLD=80
CHECK_INTERVAL=5
LOG_FILE=/var/log/cpu_monitor.log
METRICS_ENABLED=false

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password
ALERT_FROM=your_email@gmail.com
ALERT_TO=recipient@example.com
```

Secure it:

```bash
sudo chmod 600 /etc/cpu_monitor.env
```

---

### 4. Install the systemd Service

```bash
sudo cp task2_cpu_monitor/cpu_monitor.service /etc/systemd/system/cpu_monitor.service
sudo systemctl daemon-reload
sudo systemctl enable --now cpu_monitor
```

---

### 5. Check Service Status

```bash
sudo systemctl status cpu_monitor
```

Follow logs:

```bash
sudo journalctl -u cpu_monitor -f
```

Restart the service:

```bash
sudo systemctl restart cpu_monitor
```

Stop the service:

```bash
sudo systemctl stop cpu_monitor
```

---

## CPU Monitor Logic

High-level pseudo-code:

```text
Load configuration
Initialize logger
Start Prometheus metrics server if enabled

while service is running:
    Read total CPU usage
    Read per-core CPU usage
    Update metrics

    if CPU usage > threshold:
        if not already in alert state:
            Log alert
            Send email alert if SMTP is configured
            Mark system as in alert state
    else:
        if previously in alert state:
            Log recovery message
            Mark system as healthy again

    Sleep for configured interval
```

---

# Task 3 — Bonus: Multicast Explanation

## Description

The bonus task explains multicast networking and how multicast traffic can be moved between two networks.

The explanation is available here:

```text
task3_multicast/multicast_explanation.md
```

---

## Covered Topics

The multicast explanation includes:

- What multicast is
- Difference between unicast, broadcast, and multicast
- Common multicast use cases
- IGMP
- PIM-SM
- Rendezvous Point
- GRE tunneling
- AMT
- Multicast VPN
- Example bandwidth-saving scenario

---

## Example Scenario

A company wants to stream live video from headquarters to a remote branch.

With unicast:

```text
40 users × 4 Mbps = 160 Mbps
```

With multicast:

```text
1 stream × 4 Mbps = 4 Mbps
```

Multicast saves bandwidth because the sender transmits one stream, and the network replicates packets only where receivers exist.

---

# CI/CD — GitHub Actions

This repository includes a GitHub Actions workflow:

```text
.github/workflows/ci.yml
```

The CI pipeline validates the project automatically on push or pull request.

The workflow includes:

1. Installing Python dependencies
2. Running Python lint checks
3. Starting a RabbitMQ service container
4. Smoke-testing the publisher
5. Smoke-testing the CPU monitor
6. Building Docker images

---

## Run Basic Checks Manually

Install dependencies:

```bash
pip install -r task1_message_queue/requirements.txt
pip install -r task2_cpu_monitor/requirements.txt
pip install pylint
```

Run lint checks:

```bash
pylint task1_message_queue/*.py
pylint task2_cpu_monitor/*.py
```

Run publisher test:

```bash
cd task1_message_queue
docker compose up -d
python publisher.py
docker compose down
```

Run CPU monitor test:

```bash
CPU_THRESHOLD=20 CHECK_INTERVAL=2 python task2_cpu_monitor/cpu_monitor.py
```

---

# Security Notes

This project avoids hardcoding sensitive values.

Recommended practices:

- Do not commit SMTP passwords
- Do not commit `.env` files with real secrets
- Use Docker secrets for local containerized runs
- Use GitHub Actions secrets for CI/CD
- Use `/etc/cpu_monitor.env` with restricted permissions for systemd deployments
- Keep RabbitMQ credentials configurable

---

# Troubleshooting

## RabbitMQ is not ready

Check container status:

```bash
docker compose ps
```

Check logs:

```bash
docker compose logs rabbitmq
```

Restart RabbitMQ:

```bash
docker compose restart rabbitmq
```

---

## Publisher cannot connect to RabbitMQ

Check:

```bash
docker compose ps
```

Make sure these values are correct:

```text
RABBITMQ_HOST
RABBITMQ_PORT
RABBITMQ_USER
RABBITMQ_PASS
```

If running locally, usually use:

```text
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
```

If running inside Docker Compose, use the service name:

```text
RABBITMQ_HOST=rabbitmq
```

---

## Consumer receives no messages

Check that:

1. RabbitMQ is running
2. Publisher is sending to the same queue name
3. Consumer is listening to the same queue name
4. `QUEUE_NAME=ABC` is configured consistently

---

## CPU alert does not trigger

For testing, lower the threshold:

```bash
CPU_THRESHOLD=20 CHECK_INTERVAL=2 python task2_cpu_monitor/cpu_monitor.py
```

Or use the Docker Compose stress client:

```bash
cd task2_cpu_monitor
docker compose up -d --build
docker compose logs -f cpu-monitor
```

---

## Email alert does not send

Check:

```text
SMTP_HOST
SMTP_PORT
SMTP_USER
SMTP_PASS
ALERT_FROM
ALERT_TO
```

For Gmail, use a Google App Password instead of the normal Gmail password.

---

# Technologies Used

| Technology | Purpose |
|-----------|---------|
| Python | Main programming language |
| RabbitMQ | Message queue |
| pika | Python RabbitMQ client |
| psutil | CPU/system monitoring |
| smtplib | Email alerts |
| Docker | Containerization |
| Docker Compose | Local orchestration |
| Prometheus | Metrics collection |
| Grafana | Metrics visualization |
| systemd | Linux service management |
| GitHub Actions | CI/CD automation |

---

# What This Project Demonstrates

This project demonstrates:

- Python scripting for DevOps automation
- Message queue architecture
- RabbitMQ publisher/consumer pattern
- Reliable message handling
- Dead-letter queue usage
- CPU monitoring and alerting
- Docker-based local environments
- Secure configuration and secrets handling
- Metrics and observability
- Linux service deployment
- CI/CD automation
- Basic networking knowledge around multicast

---

# Assignment Mapping

| Assignment Requirement | Implemented In |
|------------------------|----------------|
| Python publisher | `task1_message_queue/publisher.py` |
| Python consumer | `task1_message_queue/consumer.py` |
| Queue/channel named `ABC` | RabbitMQ queue configuration |
| Message queue setup documentation | README + Docker Compose |
| CPU monitoring explanation | README + `cpu_monitor.py` |
| CPU alert above 80% | Configurable `CPU_THRESHOLD=80` |
| Alerting method | Logging + optional SMTP email |
| Pseudo-code / flow | README CPU monitor logic |
| Multicast explanation | `task3_multicast/multicast_explanation.md` |
| Shared repo / zip | GitHub repository |

---
