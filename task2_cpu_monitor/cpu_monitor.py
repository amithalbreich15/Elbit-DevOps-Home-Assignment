"""
Task 2 – CPU Usage Monitor Service
=====================================
Continuously monitors CPU usage and fires alerts when it exceeds a threshold.

Production features:
  - Alert hysteresis – one alert fired per high-CPU event, one recovery logged
  - Multiple alert channels: logging (always on) + SMTP email (optional)
  - All config via environment variables – no code changes needed in production
  - Prometheus metrics endpoint on :8000/metrics (enabled by default in Docker)
  - systemd-compatible (logs to stdout/stderr; clean SIGTERM handling)
  - Detailed per-core breakdown included in every alert

Author : Amit Halbreich
"""

import os
import sys
import time
import signal
import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from typing import Optional

import psutil

# ── Optional Prometheus metrics ───────────────────────────────────────────────
try:
    from prometheus_client import start_http_server, Gauge, Info, Counter
    PROMETHEUS_ENABLED = True
except ImportError:
    start_http_server = None
    Gauge = None
    Info = None
    Counter = None
    PROMETHEUS_ENABLED = False

# ── Configuration (all overridable via environment variables) ─────────────────
CPU_THRESHOLD   = float(os.getenv("CPU_THRESHOLD",   "80.0"))
CHECK_INTERVAL  = int(os.getenv("CHECK_INTERVAL",    "5"))
LOG_FILE        = os.getenv("LOG_FILE",              "")         # empty = stdout only
METRICS_PORT    = int(os.getenv("METRICS_PORT",      "8000"))
METRICS_ENABLED = os.getenv("METRICS_ENABLED",       "true").lower() == "true"
HOSTNAME        = os.getenv("HOSTNAME",              os.uname().nodename)

# SMTP / email alert settings – loaded from Docker secrets or env vars
# In Docker: mount secret files and set env vars to their paths, OR set values directly.
SMTP_HOST  = os.getenv("SMTP_HOST",  "")
SMTP_PORT  = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER  = os.getenv("SMTP_USER",  "")
SMTP_PASS  = os.getenv("SMTP_PASS",  "")   # use secret file in production
ALERT_FROM = os.getenv("ALERT_FROM", "")
ALERT_TO   = os.getenv("ALERT_TO",   "")

# ── Secret file loader ────────────────────────────────────────────────────────
def _read_secret(env_var: str, secret_path: str) -> str:
    """
    Read a secret from a Docker secret file if it exists,
    otherwise fall back to the environment variable.
    Docker mounts secrets at /run/secrets/<name> by default.
    """
    path = os.getenv(f"{env_var}_FILE", secret_path)
    if path and os.path.isfile(path):
        with open(path) as f:
            return f.read().strip()
    return os.getenv(env_var, "")

SMTP_PASS  = _read_secret("SMTP_PASS",  "/run/secrets/smtp_pass")
ALERT_TO   = _read_secret("ALERT_TO",   "/run/secrets/alert_to")

# ── Logging setup ─────────────────────────────────────────────────────────────
_log_handlers = [logging.StreamHandler(sys.stdout)]
if LOG_FILE:
    _log_handlers.append(logging.FileHandler(LOG_FILE))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
    handlers=_log_handlers,
)
log = logging.getLogger("cpu_monitor")

# ── Prometheus metrics setup ──────────────────────────────────────────────────
cpu_gauge: Optional[object]    = None
alert_counter: Optional[object] = None
build_info: Optional[object]   = None

if METRICS_ENABLED and PROMETHEUS_ENABLED:
    cpu_gauge     = Gauge("cpu_usage_percent",    "Current total CPU usage (%)")
    alert_counter = Counter("cpu_alerts_total",   "Number of high-CPU alerts fired")
    build_info    = Info("cpu_monitor_build",     "Build / version info")
    build_info.info({"version": "1.0.0", "host": HOSTNAME, "threshold": str(CPU_THRESHOLD)})

# ── Alert helpers ─────────────────────────────────────────────────────────────

def _cpu_report(cpu_total: float) -> str:
    per_core   = psutil.cpu_percent(percpu=True)
    core_lines = "\n".join(f"  Core {i}: {pct:.1f}%" for i, pct in enumerate(per_core))
    mem        = psutil.virtual_memory()
    return (
        f"Host      : {HOSTNAME}\n"
        f"Timestamp : {datetime.now().isoformat()}\n"
        f"CPU Total : {cpu_total:.1f}%   (threshold: {CPU_THRESHOLD}%)\n"
        f"Per-core  :\n{core_lines}\n"
        f"Memory    : {mem.percent:.1f}% used "
        f"({mem.used // 1024 // 1024} MB / {mem.total // 1024 // 1024} MB)\n"
    )


def send_email_alert(cpu_total: float) -> None:
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASS, ALERT_FROM, ALERT_TO]):
        log.debug("SMTP not configured – skipping email alert.")
        return
    subject = f"[ALERT] High CPU: {cpu_total:.1f}% on {HOSTNAME}"
    body    = (f"CPU usage exceeded {CPU_THRESHOLD}%.\n\n" + _cpu_report(cpu_total))
    msg             = MIMEText(body)
    msg["Subject"]  = subject
    msg["From"]     = ALERT_FROM
    msg["To"]       = ALERT_TO
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(ALERT_FROM, [ALERT_TO], msg.as_string())
        log.info("Email alert sent to %s.", ALERT_TO)
    except Exception as exc:
        log.error("Failed to send email: %s", exc)


def fire_alert(cpu_total: float) -> None:
    report = _cpu_report(cpu_total)
    log.warning("HIGH CPU ALERT – %.1f%% exceeds threshold (%.1f%%)\n%s",
                cpu_total, CPU_THRESHOLD, report)
    if alert_counter:
        alert_counter.inc()
    send_email_alert(cpu_total)


# ── Graceful shutdown ─────────────────────────────────────────────────────────
_running = True

def _handle_signal(signum, _frame):
    global _running
    log.info("Signal %s received – stopping monitor…", signum)
    _running = False

signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT,  _handle_signal)

# ── Main monitoring loop ──────────────────────────────────────────────────────

def monitor_cpu() -> None:
    log.info("CPU monitor started | threshold=%.1f%% | interval=%ds | prometheus=%s",
             CPU_THRESHOLD, CHECK_INTERVAL, METRICS_ENABLED)

    if METRICS_ENABLED and PROMETHEUS_ENABLED:
        start_http_server(METRICS_PORT)
        log.info("Prometheus metrics → http://%s:%d/metrics", HOSTNAME, METRICS_PORT)
    elif METRICS_ENABLED and not PROMETHEUS_ENABLED:
        log.warning("METRICS_ENABLED=true but prometheus_client is not installed.")

    # Warm-up (first psutil call always returns 0.0)
    psutil.cpu_percent(interval=None)
    in_alert = False

    while _running:
        cpu_total = psutil.cpu_percent(interval=1)

        if cpu_gauge is not None:
            cpu_gauge.set(cpu_total)

        if cpu_total > CPU_THRESHOLD:
            if not in_alert:
                fire_alert(cpu_total)
                in_alert = True
        else:
            if in_alert:
                log.info("CPU returned to normal: %.1f%% (threshold: %.1f%%)",
                         cpu_total, CPU_THRESHOLD)
                in_alert = False
            else:
                log.info("CPU usage: %.1f%%", cpu_total)

        # Responsive sleep – checks shutdown flag every 200ms
        remaining = max(0, CHECK_INTERVAL - 1)
        elapsed   = 0.0
        while _running and elapsed < remaining:
            time.sleep(0.2)
            elapsed += 0.2

    log.info("CPU monitor stopped cleanly.")


if __name__ == "__main__":
    monitor_cpu()
