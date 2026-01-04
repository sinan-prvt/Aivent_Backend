import jwt
import os
import sys
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from types import SimpleNamespace

class RemoteJWTAuthentication(BaseAuthentication):

    def authenticate(self, request):
        print("🔍 AUTH START", flush=True)

        auth = request.headers.get("Authorization", "")
        print(f"🔍 AUTH HEADER: {auth}", flush=True)

        if not auth.startswith("Bearer "):
            print("🔍 NO BEARER TOKEN", flush=True)
            return None

        token = auth.split(" ", 1)[1]
        print(f"🔍 RAW TOKEN: {token[:20]}...", flush=True)

        key_path = settings.JWT_PUBLIC_KEY_PATH
        print(f"🔍 KEY PATH: {key_path}", flush=True)

        try:
            with open(key_path, "r") as f:
                public_key = f.read()
            print("🔍 KEY LOADED OK", flush=True)
        except Exception as e:
            print(f"🔍 FAILED TO LOAD PUBLIC KEY: {e}", flush=True)
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
            print(f"🔍 DECODE SUCCESS: {decoded}", flush=True)
        except Exception as e:
            print(f"🔍 JWT DECODE FAILED: {e}", flush=True)
            raise AuthenticationFailed("Invalid or expired token")

        user_id = decoded.get("user_id")
        if user_id is not None:
            user_id = int(user_id)  

        # Debug MFA check
        role = decoded.get("role")
        mfa_status = decoded.get("mfa")
        print(f"🔍 MFA CHECK - Role: {role}, MFA Status: {mfa_status}", flush=True)
        
        # Disable MFA check for debugging if needed, but for now just logging it
        if role == "vendor" and not mfa_status:
             print("🔍 MFA CHECK FAILED", flush=True)
             raise AuthenticationFailed("MFA required")

        user = SimpleNamespace(
            id=user_id,
            email=decoded.get("email"),
            role=role,
            is_authenticated=True,
            is_active=True,
            is_staff=(role == "admin"),
            is_superuser=False,
        )

        print(f"🔍 AUTH USER: {user}", flush=True)
        return (user, None)
