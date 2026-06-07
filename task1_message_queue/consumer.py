"""
Task 1 – RabbitMQ Consumer
============================
Subscribes to the configured RabbitMQ queue and processes messages.

Environment variables are loaded from a local .env file when present.
Do not commit .env to Git. Commit .env.example instead.

Author: Amit Halbreich
"""

import logging
import os
import signal
import sys
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

PREFETCH_COUNT = int(os.getenv("PREFETCH_COUNT", "1"))
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
log = logging.getLogger("consumer")

_shutdown = False


def _handle_signal(signum, _frame):
    global _shutdown
    log.info("Received signal %s – shutting down gracefully…", signum)
    _shutdown = True


signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)


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


def setup_channel(connection: pika.BlockingConnection) -> pika.adapters.blocking_connection.BlockingChannel:
    """Declare queues and configure QoS."""
    channel = connection.channel()
    declare_queues(channel)
    channel.basic_qos(prefetch_count=PREFETCH_COUNT)
    return channel


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
            channel = setup_channel(connection)

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


def process_message(message: str) -> None:
    """Application-level message handler. Replace with real logic."""
    print(f"  ✔  {message}")
    time.sleep(0.05)


def on_message(
    channel: pika.adapters.blocking_connection.BlockingChannel,
    method: pika.spec.Basic.Deliver,
    properties: pika.spec.BasicProperties,
    body: bytes,
) -> None:
    """Process a single message. Nack sends failed messages to the DLQ."""
    try:
        message = body.decode("utf-8")

        log.info(
            "Received [tag=%s] [id=%s]: %s",
            method.delivery_tag,
            properties.message_id or "n/a",
            message,
        )

        process_message(message)

        channel.basic_ack(delivery_tag=method.delivery_tag)
        log.debug("ACK sent for tag %s.", method.delivery_tag)

    except Exception as exc:  # pylint: disable=broad-except
        log.error(
            "Failed to process message [tag=%s]: %s – sending to DLQ.",
            method.delivery_tag,
            exc,
        )
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_consuming() -> None:
    """Main consumer loop."""
    while not _shutdown:
        connection = None

        try:
            connection, channel = connect_with_retry()

            channel.basic_consume(
                queue=QUEUE_NAME,
                on_message_callback=on_message,
                auto_ack=False,
            )

            log.info(
                "Listening on queue '%s' (DLQ: '%s'). CTRL-C to stop.",
                QUEUE_NAME,
                DLQ_NAME,
            )

            while not _shutdown:
                connection.process_data_events(time_limit=1)

            channel.stop_consuming()
            connection.close()
            log.info("Connection closed cleanly.")
            break

        except (AMQPConnectionError, AMQPChannelError) as exc:
            if _shutdown:
                break

            log.error("Lost connection: %s – reconnecting…", exc)

            if connection and not connection.is_closed:
                connection.close()

            time.sleep(RETRY_BACKOFF)


if __name__ == "__main__":
    log.info("Consumer starting…")

    try:
        start_consuming()
    except RuntimeError as err:
        log.critical("%s", err)
        sys.exit(1)

    log.info("Consumer stopped.")
