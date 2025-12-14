import os
import requests
from django.conf import settings
from typing import Dict


RECAPTCHA_SECRET = os.environ.get("RECAPTCHA_SECRET_KEY") or getattr(settings, "RECAPTCHA_SECRET_KEY", None)
RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"
DEFAULT_MIN_SCORE = float(os.environ.get("RECAPTCHA_MIN_SCORE", 0.5))


def verify_recaptcha(token: str, remoteip: str | None = None) -> Dict:

    if not RECAPTCHA_SECRET:
        return {"success": False, "error-codes": ["missing-secret"]}

    payload = {"secret": RECAPTCHA_SECRET, "response": token}
    if remoteip:
        payload["remoteip"] = remoteip

    try:
        r = requests.post(RECAPTCHA_VERIFY_URL, data=payload, timeout=5)
        r.raise_for_status()
        data = r.json()
        return {
            "success": bool(data.get("success", False)),
            "score": data.get("score"),
            "action": data.get("action"),
            "challenge_ts": data.get("challenge_ts"),
            "hostname": data.get("hostname"),
            "error-codes": data.get("error-codes", []),
            "raw": data,
        }
    except requests.RequestException as e:
        return {"success": False, "score": None, "error-codes": ["request-failed", str(e)]}

