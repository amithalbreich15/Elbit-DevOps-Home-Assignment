# Task 2 — CPU Monitor: Docker Testing Stack

**Author:** Amit Halbreich | amithalbreich15@gmail.com  
**GitHub:** https://github.com/amithalbreich15/Elbit-DevOps-Home-Assignment

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Docker Network: monitor_net                  │
│                                                                  │
│  ┌──────────────────┐      ┌──────────────────┐                 │
│  │  stress-client   │      │   cpu-monitor    │ :8000/metrics   │
│  │  (Ubuntu 24.04)  │      │  (Ubuntu 24.04)  │◄────────────┐  │
│  │                  │      │                  │             │  │
│  │  stress-ng       │      │  cpu_monitor.py  │             │  │
│  │  generates load  │      │  + prometheus    │             │  │
│  └──────────────────┘      └──────────────────┘             │  │
│          │ CPU load on shared host                           │  │
│          ▼                                                   │  │
│  ┌──────────────────┐      ┌──────────────────┐             │  │
│  │   prometheus     │─────►│    grafana       │             │  │
│  │   :9090          │      │    :3000         │             │  │
│  │  scrapes metrics │      │  dashboards      │             │  │
│  └──────────────────┘──────┴──────────────────┘─────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start (Linux / macOS)

### 1. Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Docker | 24+ | https://docs.docker.com/get-docker/ |
| Docker Compose v2 | 2.20+ | bundled with Docker Desktop |

### 2. Configure secrets

```bash
# Fill in REAL values (these are never committed to git)
echo "your_smtp_password"      > secrets/smtp_pass
echo "alerts@yourcompany.com"  > secrets/alert_to
```

If you don't use email alerts, leave the placeholder values — the monitor
will silently skip email and only log to stdout.

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env to customise threshold, stress timing, Grafana password, etc.
```

### 4. Start the stack

```bash
docker compose up -d --build
```

### 5. Watch the monitor react to CPU stress

```bash
# Follow monitor logs
docker compose logs -f cpu-monitor

# Follow stress client logs
docker compose logs -f stress-client
```

Expected log output when stress triggers the alert:

```
2024-05-01T12:00:00 [INFO]  cpu_monitor – CPU usage: 8.2%
2024-05-01T12:00:05 [INFO]  cpu_monitor – CPU usage: 11.4%
2024-05-01T12:00:10 [WARNING] cpu_monitor – HIGH CPU ALERT – 42.7% exceeds threshold (20.0%)
  Host      : cpu_monitor
  CPU Total : 42.7%   (threshold: 20.0%)
  Per-core  :
    Core 0: 85.2%
    Core 1: 43.1%
  Memory    : 34.2% used (2734 MB / 7989 MB)
2024-05-01T12:00:45 [INFO]  cpu_monitor – CPU returned to normal: 6.1% (threshold: 20.0%)
```

---

## URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| Prometheus metrics (raw) | http://localhost:8000/metrics | none |
| Prometheus UI | http://localhost:9090 | none |
| Grafana dashboard | http://localhost:3000 | admin / (GRAFANA_PASSWORD in .env) |

### Useful Prometheus queries

```promql
# Current CPU usage
cpu_usage_percent

# Total alerts fired since container start
cpu_alerts_total

# Alert rate per minute (rolling 1-minute window)
rate(cpu_alerts_total[1m]) * 60
```

---

## Environment Variables Reference

All variables can be set in `.env` (non-sensitive) or `secrets/` (sensitive).

| Variable | Default | Description | Sensitive? |
|----------|---------|-------------|------------|
| `CPU_THRESHOLD` | `20` | Alert threshold % (low for testing) | No |
| `CHECK_INTERVAL` | `5` | Seconds between CPU samples | No |
| `METRICS_PORT` | `8000` | Prometheus metrics port | No |
| `METRICS_ENABLED` | `true` | Enable Prometheus endpoint | No |
| `SMTP_HOST` | `` | SMTP server hostname | No |
| `SMTP_PORT` | `587` | SMTP port | No |
| `SMTP_USER` | `` | SMTP username | No |
| `ALERT_FROM` | `` | Sender email address | No |
| `SMTP_PASS` | — | SMTP password | **Yes** → `secrets/smtp_pass` |
| `ALERT_TO` | — | Alert recipient email | **Yes** → `secrets/alert_to` |
| `STRESS_DURATION` | `30` | Stress client: seconds of CPU load | No |
| `IDLE_DURATION` | `20` | Stress client: seconds of idle | No |
| `CPU_WORKERS` | `2` | Stress client: parallel workers | No |
| `GRAFANA_USER` | `admin` | Grafana admin username | No |
| `GRAFANA_PASSWORD` | `changeme` | Grafana admin password | **Change in .env** |

---

## Windows Setup

### Option A – Linux containers on Windows (recommended)

Docker Desktop on Windows can run Linux containers natively via WSL 2.
All commands above work identically in PowerShell or WSL:

```powershell
docker compose up -d --build
docker compose logs -f cpu-monitor
```

### Option B – Native Windows container image

> Requires Docker Desktop switched to **Windows containers mode**.  
> Right-click Docker tray icon → "Switch to Windows containers"

```powershell
# Build the Windows image
docker build -f Dockerfile.windows -t cpu-monitor:windows .

# Run standalone (no compose – Windows containers can't mix with Linux)
docker run --rm -p 8000:8000 `
  -e CPU_THRESHOLD=20 `
  -e METRICS_ENABLED=true `
  cpu-monitor:windows
```

> **Note:** The full stack (Prometheus + Grafana) runs as Linux containers.
> Use Option A (Linux containers on Windows) for the complete testing experience.

---

## Stopping the Stack

```bash
docker compose down          # keep Prometheus/Grafana data volumes
docker compose down -v       # remove all volumes (fresh start)
```

---

## Production Notes

Before deploying to production:

1. **Raise the threshold**: set `CPU_THRESHOLD=80` in `.env`
2. **Set real secrets**: update `secrets/smtp_pass` and `secrets/alert_to`
3. **Change Grafana password**: set a strong `GRAFANA_PASSWORD` in `.env`
4. **Remove stress-client**: comment it out in `docker-compose.yml`
5. **Consider Prometheus retention**: default is 7 days (`--storage.tsdb.retention.time`)
