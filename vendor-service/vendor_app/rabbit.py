import os
import json
import pika
import logging

logger = logging.getLogger(__name__)
RABBIT_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
EXCHANGE = os.getenv("EVENT_EXCHANGE", "aivent.events")

def _get_connection():
    params = pika.URLParameters(RABBIT_URL)
    params.heartbeat = 600
    params.blocked_connection_timeout = 30
    return pika.BlockingConnection(params)

def publish_event(routing_key: str, payload: dict):
    try:
        conn = _get_connection()
        channel = conn.channel()

        channel.exchange_declare(exchange=EXCHANGE, exchange_type='topic', durable=True)
        body = json.dumps(payload, default=str)
        channel.basic_publish(
            exchange=EXCHANGE,
            routing_key=routing_key,
            body=body,
            properties=pika.BasicProperties(content_type='application/json', delivery_mode=2)
        )
        conn.close()
    except Exception:
        logger.exception("Failed to publish event %s", routing_key)
        raise
