import json
import pika
from django.conf import settings


def publish_event(routing_key, payload):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=settings.RABBITMQ_HOST)
    )
    channel = connection.channel()
    channel.exchange_declare(exchange="catalog.events", exchange_type="topic", durable=True)

    channel.basic_publish(
        exchange="catalog.events",
        routing_key=routing_key,
        body=json.dumps(payload),
    )

    connection.close()
