import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vendor_project.settings")
django.setup()
import time
import json
import pika
import logging
from django.db import close_old_connections
from vendor_app.models import VendorProfile

logger = logging.getLogger(__name__)

RABBIT_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
EXCHANGE = os.getenv("EVENT_EXCHANGE", "aivent.events")
QUEUE = "vendor-service-queue"


def handle_event(routing_key, payload):
    close_old_connections()

    if routing_key == "vendor.created":
        VendorProfile.objects.get_or_create(
            user_id=payload["user_id"],
            defaults={
                "phone": payload.get("phone"),
                "status": "pending",
            },
        )

    elif routing_key == "vendor.approved":
        VendorProfile.objects.filter(
            user_id=payload["user_id"]
        ).update(status="approved")

    elif routing_key == "vendor.rejected":
        VendorProfile.objects.filter(
            user_id=payload["user_id"]
        ).update(status="rejected")


def _consume():
    while True:
        try:
            logger.info("Connecting to RabbitMQ...")
            params = pika.URLParameters(RABBIT_URL)
            conn = pika.BlockingConnection(params)
            channel = conn.channel()

            channel.exchange_declare(
                exchange=EXCHANGE,
                exchange_type="topic",
                durable=True,
            )

            channel.queue_declare(queue=QUEUE, durable=True)
            channel.queue_bind(
                queue=QUEUE,
                exchange=EXCHANGE,
                routing_key="vendor.*",
            )

            def callback(ch, method, properties, body):
                payload = json.loads(body)
                handle_event(method.routing_key, payload)
                ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_consume(queue=QUEUE, on_message_callback=callback)
            logger.info("Vendor event consumer started")
            channel.start_consuming()

        except Exception as e:
            logger.exception("Consumer crashed, retrying in 5s")
            time.sleep(5)


if __name__ == "__main__":
    _consume()
