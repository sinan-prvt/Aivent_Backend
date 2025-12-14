from django.db import models
from auth_app.models import User


class UserProfile(models.Model):
    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    full_name = models.CharField(max_length=150, blank=True, null=True) 
    phone = models.CharField(max_length=20, blank=True, null=True) 
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True) 
    dob = models.DateField(blank=True, null=True) 
    
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True) 
    
    country = models.CharField(max_length=100, blank=True, null=True) 
    state = models.CharField(max_length=100, blank=True, null=True) 
    city = models.CharField(max_length=100, blank=True, null=True) 
    pincode = models.CharField(max_length=20, blank=True, null=True) 
    full_address = models.TextField(blank=True, null=True) 
    
    created_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now=True) 
    
    def __str__(self): 
        return f"Profile for user {self.user_id}"


