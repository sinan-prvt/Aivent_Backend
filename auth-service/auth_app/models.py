from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager
from django.conf import settings    
import uuid
import pyotp
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields): 
        email = self.normalize_email(email) 
        extra_fields.setdefault("username", extra_fields.get("username") or email.split("@")[0]) 
        extra_fields.setdefault("role", "admin") 
        extra_fields.setdefault("email_verified", True) 
        extra_fields.setdefault("vendor_approved", True) 
        extra_fields.setdefault("is_staff", True) 
        extra_fields.setdefault("is_superuser", True) 
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True) 
    username = models.CharField(max_length=150, unique=True) 
    full_name = models.CharField(max_length=150, blank=True, null=True) 
    phone = models.CharField(max_length=20, blank=True, null=True) 
    remote_id = models.CharField(max_length=64, blank=True, null=True, unique=True) 
    
    role = models.CharField( max_length=20, default="customer", choices=[ ("customer", "Customer"), ("vendor", "Vendor"), ("admin", "Admin") ] ) 
    date_joined = models.DateTimeField(default=timezone.now, editable=False)

    email_verified = models.BooleanField(default=False) 
    vendor_approved = models.BooleanField(default=False) 
    
    is_active = models.BooleanField(default=True) 
    is_staff = models.BooleanField(default=False) 
    
    totp_secret = models.CharField(max_length=64, blank=True, null=True)   # store base32 secret
    totp_enabled = models.BooleanField(default=False)  

    USERNAME_FIELD = "email" 
    REQUIRED_FIELDS = ["username"] 
    
    objects = UserManager() 
    
    def __str__(self): 
        return self.email


class OTP(models.Model): 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) 
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) 
    
    otp_hash = models.CharField(max_length=64) 
    salt = models.CharField(max_length=64) 
    purpose = models.CharField(max_length=50) 
    
    created_at = models.DateTimeField(auto_now_add=True) 
    expires_at = models.DateTimeField() 
    used = models.BooleanField(default=False)

