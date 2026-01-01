import os
import sys
import time
import json
import logging
import pika

sys.path.append("/app")

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vendor_project.settings")
django.setup()

from django.db import transaction, IntegrityError, close_old_connections
from vendor_app.models import Notification

logger = logging.getLogger(__name__)

RABBIT_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
EXCHANGE = os.getenv("EVENT_EXCHANGE", "catalog.events")
QUEUE = "vendor-service-queue"


def handle_catalog_event(ch, method, properties, body):
    try:
        event = json.loads(body)
    except json.JSONDecodeError:
        logger.error("Invalid JSON received, acknowledging to discard")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    # Hard validation
    required = {"event_id", "event_type", "vendor_id", "payload"}
    if not required.issubset(event):
        logger.warning(f"⚠️ Invalid event structure, skipping: {event}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    try:
        with transaction.atomic():
            Notification.objects.create(
                vendor_id=event["vendor_id"],
                event_id=event["event_id"],
                event_type=event["event_type"],
                title=_get_title(event["event_type"]),
                message=_get_message(event["event_type"], event["payload"]),
            )
        logger.info(f"Processed event {event['event_id']}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except IntegrityError:
        # Idempotent duplicate - we already processed this event_id
        logger.info(f"Duplicate event {event['event_id']} detected, ignoring safely")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logger.exception(f"Error processing event {event.get('event_id')}: {e}")
        # Requeue for retry
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    finally:
        close_old_connections()


def _get_title(event_type):
    return {
        "PRODUCT_CREATED": "Product submitted",
        "PRODUCT_APPROVED": "Product approved 🎉",
        "PRODUCT_REJECTED": "Product rejected ❌",
    }.get(event_type, "Notification")


def _get_message(event_type, payload):
    name = payload.get("name", "")
    return {
        "PRODUCT_CREATED": f"Your product '{name}' was submitted for review.",
        "PRODUCT_APPROVED": f"Your product '{name}' is now live.",
        "PRODUCT_REJECTED": f"Your product '{name}' was rejected.",
    }.get(event_type, "You have a new notification.")


def _consume():
    while True:
        try:
            logger.info("Connecting to RabbitMQ...")
            # Heartbeat is important for long running connections
            params = pika.URLParameters(RABBIT_URL + "?heartbeat=600") 
            conn = pika.BlockingConnection(params)
            channel = conn.channel()

            channel.exchange_declare(
                exchange=EXCHANGE,
                exchange_type="fanout",
                durable=True,
            )

            channel.queue_declare(queue=QUEUE, durable=True)
            channel.queue_bind(
                queue=QUEUE,
                exchange=EXCHANGE,
            )

            # Set prefetch count to 1 to ensure fair dispatch
            channel.basic_qos(prefetch_count=1)

            channel.basic_consume(queue=QUEUE, on_message_callback=handle_catalog_event)
            logger.info("Vendor event consumer started")
            channel.start_consuming()

        except Exception:
            logger.exception("Consumer crashed, retrying in 5s")
            time.sleep(5)


if __name__ == "__main__":
    _consume()
