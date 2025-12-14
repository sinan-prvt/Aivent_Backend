import jwt
import os
import logging
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from types import SimpleNamespace

logger = logging.getLogger("vendor_auth")

class RemoteJWTAuthentication(BaseAuthentication):

    def authenticate(self, request):
        logger.info("AUTH START")

        auth = request.headers.get("Authorization", "")
        logger.info(f"AUTH HEADER: {auth}")

        if not auth.startswith("Bearer "):
            logger.info("NO BEARER TOKEN")
            return None

        token = auth.split(" ", 1)[1]
        logger.info(f"RAW TOKEN: {token[:40]}...")

        key_path = settings.JWT_PUBLIC_KEY_PATH
        logger.info(f"KEY PATH: {key_path}")

        try:
            with open(key_path, "r") as f:
                public_key = f.read()
            logger.info("KEY LOADED OK")
        except Exception as e:
            logger.exception("FAILED TO LOAD PUBLIC KEY")
            raise AuthenticationFailed("Server key configuration error")

        try:
            decoded = jwt.decode(
                token,
                public_key,
                algorithms=[settings.JWT_ALGORITHM],
                issuer="aivent-auth",
                audience="aivent-services",
                options={"verify_exp": True},
            )
            logger.info(f"DECODE SUCCESS: {decoded}")
        except Exception as e:
            logger.exception("JWT DECODE FAILED")
            raise AuthenticationFailed("Invalid or expired token")

        user = SimpleNamespace(
            id=decoded.get("id"),
            email=decoded.get("email"),
            role=decoded.get("role"),
            is_authenticated=True, 
        )

        logger.info(f"AUTH USER: {user}")
        return (user, None)
