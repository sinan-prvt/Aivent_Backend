# auth_app/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTP
from user_app.models import UserProfile

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "username", "role", "email_verified", "vendor_approved", "is_active", "is_staff")
    list_filter = ("role", "email_verified", "vendor_approved", "is_active", "is_staff")
    search_fields = ("email", "username", "full_name", "phone")
    ordering = ("email",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal", {"fields": ("username", "full_name", "phone")}),
        ("Permissions", {"fields": ("role", "is_active", "is_staff", "is_superuser")}),
        ("Verification", {"fields": ("email_verified", "vendor_approved", "totp_enabled")}),
        ("TOTP", {"fields": ("totp_secret",)}),
    )
    readonly_fields = ("date_joined",)


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "purpose", "created_at", "expires_at", "used")
    search_fields = ("user__email", "purpose")
    list_filter = ("purpose", "used")
