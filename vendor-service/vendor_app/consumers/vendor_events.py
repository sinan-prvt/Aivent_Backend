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
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)
print("🚀 Vendor event consumer script starting...", flush=True)

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
        target_role = None
        if event["event_type"] in ["VENDOR_APPLIED", "PRODUCT_CREATED"]:
            target_role = "admin"

        with transaction.atomic():
            Notification.objects.create(
                vendor_id=event["vendor_id"],
                target_role=target_role,
                event_id=event["event_id"],
                event_type=event["event_type"],
                title=_get_title(event["event_type"], target_role),
                message=_get_message(event["event_type"], event["payload"], target_role),
            )
        
        # Broadcast to WebSocket
        channel_layer = get_channel_layer()

        if target_role == "admin":
            # Broadcast ONLY to admins
            async_to_sync(channel_layer.group_send)(
                "role_admin",
                {
                    "type": "notify_new",
                    "notification": {
                        "id": event["event_id"],
                        "event_type": event["event_type"],
                        "title": _get_title(event["event_type"], "admin"),
                        "message": f"Vendor {event['vendor_id']}: {_get_message(event['event_type'], event['payload'], 'admin')}",
                    }
                }
            )
        else:
            # Broadcast ONLY to the specific vendor
            async_to_sync(channel_layer.group_send)(
                f"user_{event['vendor_id']}",
                {
                    "type": "notify_new",
                    "notification": {
                        "id": event["event_id"],
                        "event_type": event["event_type"],
                        "title": _get_title(event["event_type"], "vendor"),
                        "message": _get_message(event["event_type"], event["payload"], "vendor"),
                    }
                }
            )

        logger.info(f"Processed and broadcast event {event['event_id']}")
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


def _get_title(event_type, target_role=None):
    titles = {
        "PRODUCT_CREATED": "New Product Submitted" if target_role == "admin" else "Product Submitted",
        "PRODUCT_APPROVED": "Product Approved 🎉",
        "PRODUCT_REJECTED": "Product Rejected ❌",
        "VENDOR_APPLIED": "New Vendor Application",
        "VENDOR_APPROVED": "Application Approved 🎉",
        "BOOKING_NEW": "New Booking Received 📅",
    }
    return titles.get(event_type, "Notification")


def _get_message(event_type, payload, target_role=None):
    name = payload.get("name", "")
    if event_type == "PRODUCT_CREATED":
        if target_role == "admin":
            return f"New product '{name}' submitted for review."
        return f"Your product '{name}' was submitted for review."

    if event_type == "VENDOR_APPLIED":
        if target_role == "admin":
            return "A new vendor application has been received."
        return "Your vendor application has been submitted."

    messages = {
        "PRODUCT_APPROVED": f"Your product '{name}' is now live.",
        "PRODUCT_REJECTED": f"Your product '{name}' was rejected.",
        "VENDOR_APPROVED": f"Welcome! Your vendor application has been approved.",
        "BOOKING_NEW": f"You have a new booking request for your service.",
    }
    return messages.get(event_type, "You have a new notification.")


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
