from urllib.parse import parse_qs
import jwt
import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def get_user_from_token(token):
    try:
        key_path = settings.JWT_PUBLIC_KEY_PATH
        with open(key_path, "r") as f:
            public_key = f.read()

        payload = jwt.decode(
            token,
            public_key,
            algorithms=[settings.JWT_ALGORITHM],
            audience="aivent-services",
        )

        return {
            "user_id": payload["user_id"],
            "role": payload.get("role"),
        }

    except Exception as e:
        logger.warning(f"WebSocket JWT failed: {e}")
        return None

class JWTAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query = parse_qs(scope["query_string"].decode())
        token = query.get("token", [None])[0]

        scope["user"] = get_user_from_token(token) if token else None

        return await self.inner(scope, receive, send)
