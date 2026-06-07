"""
Task 1 – RabbitMQ Publisher
============================
Sends configurable persistent messages to the configured RabbitMQ queue.

Environment variables are loaded from a local .env file when present.
Do not commit .env to Git. Commit .env.example instead.

Author: Amit Halbreich
"""

import logging
import os
import time
from pathlib import Path

import pika
from pika.exceptions import AMQPChannelError, AMQPConnectionError

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).with_name(".env"))
except ImportError:
    # python-dotenv is optional. Real environment variables still work.
    pass


# ── Configuration ─────────────────────────────────────────────────────────────
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")

QUEUE_NAME = os.getenv("QUEUE_NAME", "ABC")
DLQ_NAME = os.getenv("DLQ_NAME", f"{QUEUE_NAME}.dlq")

NUM_MESSAGES = int(os.getenv("NUM_MESSAGES", "10"))
MESSAGE_DELAY = float(os.getenv("MESSAGE_DELAY", "0.5"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "5"))
RETRY_BACKOFF = float(os.getenv("RETRY_BACKOFF", "2.0"))

QUEUE_ARGUMENTS = {
    "x-dead-letter-exchange": "",
    "x-dead-letter-routing-key": DLQ_NAME,
}


# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
)
log = logging.getLogger("publisher")


def build_connection_params() -> pika.ConnectionParameters:
    """Build RabbitMQ connection parameters from environment variables."""
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    return pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300,
    )


def declare_queues(channel: pika.adapters.blocking_connection.BlockingChannel) -> None:
    """Declare DLQ and main queue with matching arguments."""
    channel.queue_declare(queue=DLQ_NAME, durable=True)

    channel.queue_declare(
        queue=QUEUE_NAME,
        durable=True,
        arguments=QUEUE_ARGUMENTS,
    )


def connect_with_retry() -> tuple[
    pika.BlockingConnection,
    pika.adapters.blocking_connection.BlockingChannel,
]:
    """Attempt to connect to RabbitMQ with exponential back-off."""
    delay = RETRY_BACKOFF

    for attempt in range(1, MAX_RETRIES + 1):
        connection = None

        try:
            log.info(
                "Connecting to RabbitMQ at %s:%s as user '%s' (attempt %d/%d)…",
                RABBITMQ_HOST,
                RABBITMQ_PORT,
                RABBITMQ_USER,
                attempt,
                MAX_RETRIES,
            )

            connection = pika.BlockingConnection(build_connection_params())
            channel = connection.channel()

            declare_queues(channel)
            channel.confirm_delivery()

            log.info("Connected successfully and queues declared.")
            return connection, channel

        except (AMQPConnectionError, AMQPChannelError) as exc:
            log.warning("RabbitMQ connection/channel failed: %s", exc)

            if connection and not connection.is_closed:
                connection.close()

            if attempt < MAX_RETRIES:
                log.info("Retrying in %.1fs…", delay)
                time.sleep(delay)
                delay = min(delay * 2, 60)
            else:
                break

    raise RuntimeError(f"Could not connect to RabbitMQ after {MAX_RETRIES} attempts.")


def publish_messages(num_messages: int = NUM_MESSAGES) -> None:
    """Publish persistent messages to the configured RabbitMQ queue."""
    connection = None

    try:
        connection, channel = connect_with_retry()

        log.info("Publishing %d messages to queue '%s'…", num_messages, QUEUE_NAME)

        for i in range(1, num_messages + 1):
            body = (
                f"Message #{i:03d} | queue={QUEUE_NAME} | "
                f"ts={time.strftime('%Y-%m-%dT%H:%M:%S')}"
            )

            channel.basic_publish(
                exchange="",
                routing_key=QUEUE_NAME,
                body=body.encode("utf-8"),
                properties=pika.BasicProperties(
                    delivery_mode=pika.DeliveryMode.Persistent,
                    content_type="text/plain",
                    message_id=f"msg-{i:04d}",
                ),
                mandatory=True,
            )

            log.info("Sent [%d/%d]: %s", i, num_messages, body)
            time.sleep(MESSAGE_DELAY)

        log.info("All %d messages published successfully.", num_messages)

    except (AMQPChannelError, AMQPConnectionError, RuntimeError) as exc:
        log.error("Publish failed: %s", exc)
        raise

    finally:
        if connection and not connection.is_closed:
            connection.close()
            log.info("Connection closed.")


if __name__ == "__main__":
    publish_messages()
