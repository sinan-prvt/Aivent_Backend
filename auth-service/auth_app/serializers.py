from rest_framework import serializers 
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer 
from auth_app.core.recaptcha import verify_recaptcha 
from auth_app.core.captcha_utils import increment_failed_attempts, reset_failed_attempts, requires_captcha 
from django.conf import settings 
from django.contrib.auth import get_user_model, authenticate
from auth_app.utils import create_otp_for_user
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token["iss"] = "aivent-auth"
        token["aud"] = "aivent-services"
        token["role"] = user.role
        token["user_id"] = str(user.id)

        return token



class CustomLoginSerializer(CustomTokenObtainPairSerializer):
    username_field = "email"

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user = User.objects.filter(email=email).first()

        if not user or not user.check_password(password):
            raise serializers.ValidationError({
                "auth": ["Invalid email or password"]
            })

        if user.role != "admin" and not user.email_verified:
            raise serializers.ValidationError({
                "email": ["Please verify email first."]
            })

        self._validated_user = user

        if user.role == "vendor" and not user.vendor_approved:
            raise serializers.ValidationError({
                "vendor": ["Vendor not approved by admin yet."]
            })

        attrs["username"] = email
        data = super().validate(attrs)

        data["user"] = {
            "id": user.id,
            "email": user.email,
            "role": user.role,
        }

        return data



class RegisterSerializer(serializers.ModelSerializer):
    recaptcha_token = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, write_only=True
    )

    class Meta:
        model = User
        fields = ["email", "password", "username", "phone", "recaptcha_token"]
        extra_kwargs = {
            "password": {"write_only": True}
        }

    def validate(self, attrs):
        request = self.context.get('request')
        ip = request.META.get('REMOTE_ADDR') if request else None
        key = ip or attrs.get('email') or 'anon'

        token = attrs.get("recaptcha_token") or (request.data.get("recaptcha_token") if request else None)

        if requires_captcha(key):
            if not token:
                raise serializers.ValidationError({
                    "recaptcha_token": ["reCAPTCHA token missing"]
                })

            resp = verify_recaptcha(token, remoteip=ip)

            if not resp.get("success") or (resp.get("score") or 0.0) < float(settings.RECAPTCHA_MIN_SCORE):
                increment_failed_attempts(key)
                raise serializers.ValidationError({
                    "recaptcha_token": ["reCAPTCHA validation failed"]
                })

        return attrs

    def create(self, validated_data):
        validated_data.pop("recaptcha_token", None)
        password = validated_data.pop("password")
        user = User(
            **validated_data,
            role="customer",
            vendor_approved=False,
            is_active=False,
            email_verified=False
        )
        user.set_password(password)
        user.save()
        return user

    
class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id", "username", "email", "full_name",
            "phone", "role", "email_verified",
            "vendor_approved", "is_active", "date_joined"
        )


class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.CharField()


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.CharField()
    otp = serializers.CharField()


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(min_length=8)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)

    

class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer used for listing user info in admin UI."""
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "full_name",
            "phone",
            "role",
            "email_verified",
            "vendor_approved",
            "is_active",
            "is_staff",
            "totp_enabled",
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined", "is_staff"]


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """Used for partial updates from admin panel (promote/demote, approve vendor)."""
    class Meta:
        model = User
        fields = [
            "email",
            "username",
            "full_name",
            "phone",
            "role",
            "email_verified",
            "vendor_approved",
            "is_active",
            "totp_enabled",
        ]
        read_only_fields = ["email"]
