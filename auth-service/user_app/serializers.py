from rest_framework import serializers 
from user_app.models import UserProfile 
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from auth_app.models import User


from rest_framework import serializers
from user_app.models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    phone = serializers.CharField(source="user.phone", required=False, allow_null=True, allow_blank=True)
    full_name = serializers.CharField(source="user.full_name", required=False, allow_blank=True)

    email = serializers.ReadOnlyField(source="user.email")
    user_created_at = serializers.ReadOnlyField(source="user.date_joined")

    class Meta:
        model = UserProfile
        fields = [
            "username",
            "full_name",
            "email",
            "phone",
            "gender",
            "dob",
            "country",
            "state",
            "city",
            "pincode",
            "full_address",
            "created_at",
            "updated_at",
            "user_created_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


    def update(self, instance, validated_data):
        """Update both UserProfile and User model"""
        user_data = validated_data.pop("user", {})

        user = instance.user
        if "username" in user_data:
            user.username = user_data["username"]

        if "phone" in user_data:
            user.phone = user_data["phone"]

        if "full_name" in user_data:
            user.full_name = user_data["full_name"]

        user.save()

        return super().update(instance, validated_data)



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer): 
    @classmethod 
    def get_token(cls, user): 
        token = super().get_token(user)

        token["id"] = str(user.id) 
        token["email"] = user.email 
        token["username"] = user.username 
        token["role"] = user.role 
        token["phone"] = user.phone 
        token["vendor_approved"] = user.vendor_approved

        return token