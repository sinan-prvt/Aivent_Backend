from rest_framework import generics
from rest_framework.response import Response 
from django.contrib.auth import get_user_model 
from .serializers import ( UserProfileSerializer, ) 
from rest_framework.views import APIView 
from .permissions import IsVendor, IsAdmin, IsCustomer 
from rest_framework import permissions 
from rest_framework.parsers import MultiPartParser, FormParser 
from user_app.models import UserProfile 
from rest_framework_simplejwt.views import TokenObtainPairView 
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404


User = get_user_model()



class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        serializer = UserProfileSerializer(profile, context={"request": request})
        return Response(serializer.data)

    def patch(self, request):
        profile = request.user.profile
        serializer = UserProfileSerializer(
            profile, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class CustomerProfileRequestView(APIView):
    """
    Allow Vendors to fetch customer profile by ID
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        # In a real app, maybe check if this vendor has a booking with this user?
        # For now, just return public info
        user = get_object_or_404(User, id=user_id)
        
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            return Response({"detail": "Profile not found"}, status=404)
        
        serializer = UserProfileSerializer(profile, context={"request": request})
        return Response(serializer.data)


class VendorDashboardView(APIView): 
    permission_classes = [IsVendor] 
    
    def get(self, request): 
        return Response({"message": "Vendor dashboard"}) 
    

class AdminPanelView(APIView): 
    permission_classes = [IsAdmin] 
    
    def get(self, request): 
        return Response({"message": "Admin Panel"}) 


class CustomerHistoryView(APIView): 
    permission_classes = [IsCustomer] 
    
    def get(self, request): 
        return Response({"orders": []})
