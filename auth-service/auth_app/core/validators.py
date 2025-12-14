from rest_framework import serializers
from auth_app.core.recaptcha import verify_recaptcha
from django.conf import settings


MIN_SCORE = float(getattr(settings, "RECAPTCHA_MIN_SCORE", 0.5))


class ReCaptchaV3Validator:

    def __init__(self, message=None, min_score=None):
        self.message = message or "reCAPTCHA verification failed"
        self.min_score = float(min_score) if min_score is not None else MIN_SCORE

    def __call__(self, value):
        if not value:
            raise serializers.ValidationError("reCAPTCHA token is required")

        request = getattr(self, "request", None)
        remoteip = None
        if request is None:
            pass

        resp = verify_recaptcha(value, remoteip=remoteip)
        if not resp.get("success"):
            raise serializers.ValidationError(self.message)
        score = resp.get("score", 0.0) or 0.0
        if score < self.min_score:
            raise serializers.ValidationError(f"reCAPTCHA score {score:.2f} below threshold {self.min_score}")
        return True

