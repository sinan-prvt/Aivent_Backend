from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import pika
from celery.result import AsyncResult
from django.conf import settings

def health_check(request):

    # DB Check
    try:
        connection.ensure_connection()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    # Redis Check
    try:
        cache.set("health", "ok", 5)
        redis_ok = cache.get("health")
        redis_status = "connected" if redis_ok == "ok" else "error"
    except Exception as e:
        redis_status = f"error: {str(e)}"

    # RabbitMQ Check
    try:
        params = pika.URLParameters(settings.CELERY_BROKER_URL)
        connection_rabbit = pika.BlockingConnection(params)
        connection_rabbit.close()
        rabbit_status = "connected"
    except Exception as e:
        rabbit_status = f"error: {str(e)}"

    # Celery Check
    try:
        from auth_app.tasks import send_email_task
        test_task = send_email_task.delay("Health Check", "OK", ["example@example.com"])
        celery_status = "running"
    except Exception as e:
        celery_status = f"error: {str(e)}"

    return JsonResponse({
        "status": "ok",
        "services": {
            "database": db_status,
            "redis": redis_status,
            "rabbitmq": rabbit_status,
            "celery": celery_status,
        }
    })
