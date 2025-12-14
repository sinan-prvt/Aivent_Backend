import secrets, hashlib
from datetime import timedelta
from django.utils import timezone
from vendor_app.models import VendorApplicationOTP

OTP_LEN = 6

def generate_otp():
    return ''.join(secrets.choice("0123456789") for _ in range(OTP_LEN))

def make_otp_hash(otp, salt):
    return hashlib.sha256(f"{otp}{salt}".encode()).hexdigest()

def create_vendor_otp_for(vendor, expiry_seconds=600):
    otp = generate_otp()
    salt = secrets.token_hex(16)
    otp_hash = make_otp_hash(otp, salt)
    otp_obj = VendorApplicationOTP.objects.create(
        vendor=vendor,
        otp_hash=otp_hash,
        salt=salt,
        expires_at=timezone.now() + timedelta(seconds=expiry_seconds)
    )
    return otp, otp_obj

def verify_vendor_otp(otp_obj, otp):
    return make_otp_hash(otp, otp_obj.salt) == otp_obj.otp_hash
