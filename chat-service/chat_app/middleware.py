from urllib.parse import parse_qs
import jwt
import os
import logging

logger = logging.getLogger(__name__)


PUBLIC_KEY_PATH = "/app/keys/public.pem"


def get_user_from_token(token):
    try:
        with open(PUBLIC_KEY_PATH) as f:
            public_key = f.read()

        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience="aivent-services",
        )

        return {
            "user_id": payload["user_id"],
            "role": payload.get("role"),
            "vendor_id": payload.get("vendor_id") or (payload["user_id"] if payload.get("role") == "vendor" else None),
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
