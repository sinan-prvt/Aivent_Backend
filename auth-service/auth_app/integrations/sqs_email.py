import json
import boto3
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def get_sqs_client():
    """
    Lazily create SQS client.
    Never create boto3 clients at import time.
    """
    if not settings.AWS_REGION:
        raise RuntimeError("AWS_REGION is not set")

    if not settings.EMAIL_QUEUE_URL:
        raise RuntimeError("EMAIL_QUEUE_URL is not set")

    return boto3.client(
        "sqs",
        region_name=settings.AWS_REGION,
    )


def send_email_via_sqs(*, subject: str, to_email: str, template: str, data: dict):
    if not to_email:
        raise ValueError("to_email is required")

    sqs = get_sqs_client()  # ✅ created at runtime

    payload = {
        "subject": subject,
        "to": to_email,
        "template": template,
        "data": data,
        "source": "auth-service",
    }

    try:
        resp = sqs.send_message(
            QueueUrl=settings.EMAIL_QUEUE_URL,
            MessageBody=json.dumps(payload),
            MessageAttributes={
                "template": {
                    "DataType": "String",
                    "StringValue": template,
                }
            },
        )

        logger.info(
            "Email enqueued to SQS",
            extra={
                "message_id": resp["MessageId"],
                "template": template,
                "to": to_email,
            },
        )

        return resp["MessageId"]

    except Exception:
        logger.exception("Failed to enqueue email to SQS")
        raise
