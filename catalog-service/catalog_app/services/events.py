import json
import pika
import os
import uuid

RABBIT_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
EXCHANGE = "catalog.events"


def publish_catalog_event(event_type, vendor_id, payload):
    params = pika.URLParameters(RABBIT_URL)
    conn = pika.BlockingConnection(params)
    channel = conn.channel()

    channel.exchange_declare(
        exchange="catalog.events",
        exchange_type="fanout",
        durable=True,
    )

    body = {
        "event_id": str(uuid.uuid4()),          # 🔑 REQUIRED
        "event_type": event_type,               # 🔑 REQUIRED
        "vendor_id": vendor_id,                 # 🔑 REQUIRED
        "payload": payload                      # 🔑 REQUIRED
    }

    channel.basic_publish(
        exchange="catalog.events",
        routing_key="",   # ignored in fanout
        body=json.dumps(body),
    )

    conn.close()
