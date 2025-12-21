from celery import shared_task
import logging
from .rabbit import publish_event

logger = logging.getLogger(__name__)



@shared_task(bind=True, max_retries=3)
def publish_event_task(self, routing_key, payload):
    try:
        publish_event(routing_key, payload)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=10)