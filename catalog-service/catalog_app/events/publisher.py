import json
import uuid
import pika
import os
import logging

logger = logging.getLogger(__name__)

RABBIT_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
EXCHANGE = "catalog.events"


def publish_catalog_event(event_type: str, vendor_id: int, payload: dict):
    """
    Canonical catalog → vendor event publisher
    """

    body = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "vendor_id": vendor_id,
        "payload": payload,
    }

    try:
        connection = pika.BlockingConnection(
            pika.URLParameters(RABBIT_URL)
        )
        channel = connection.channel()

        channel.exchange_declare(
            exchange=EXCHANGE,
            exchange_type="fanout",
            durable=True,
        )

        channel.basic_publish(
            exchange=EXCHANGE,
            routing_key="",
            body=json.dumps(body),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,
            ),
        )

        connection.close()

    except Exception:
        logger.exception("Failed to publish catalog event")
        raise
