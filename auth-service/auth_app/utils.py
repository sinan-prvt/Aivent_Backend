import secrets
import hashlib
from datetime import timedelta
from django.utils import timezone
from .models import OTP
import qrcode
import io
import base64

OTP_LENGTH = 6


def generate_otp():
    return ''.join(secrets.choice("0123456789") for _ in range(OTP_LENGTH))


def make_otp_hash(otp, salt):
    return hashlib.sha256(f"{otp}{salt}".encode()).hexdigest()


def create_otp_for_user(user, purpose, expiry=600):
    otp = generate_otp()
    salt = secrets.token_hex(16)
    otp_hash = make_otp_hash(otp, salt)

    otp_obj = OTP.objects.create(
        user=user,
        otp_hash=otp_hash,
        salt=salt,
        purpose=purpose,
        expires_at=timezone.now() + timedelta(seconds=expiry)
    )
    return otp, otp_obj


def verify_otp_entry(otp_obj, otp_value):
    candidate_hash = make_otp_hash(otp_value, otp_obj.salt)
    if candidate_hash != otp_obj.otp_hash:
        return False

    otp_obj.used = True
    otp_obj.save()
    return True


def qrcode_base64_from_uri(uri):
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return "data:image/png;base64," + b64
