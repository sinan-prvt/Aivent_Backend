from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views.auth import (
    RegisterView,
    MeView,
    CustomLoginView,
    LogoutView,
    LogoutAllView,
    ChangePasswordView,
    CustomTokenObtainPairView,
)
from .views.otp import (
    SendOTPView,
    VerifyOTPView,
    SendResetOTPView,
)
from .views.password import ResetPasswordView
from .views.social import GoogleLoginView, MicrosoftAuthView
from .views.health import health_check
from .views.verify_mfa import VerifyMFAView
from .views.internal_users import InternalUserByEmail

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),

    path("register/", RegisterView.as_view(), name="auth-register"),
    path("send-otp/", SendOTPView.as_view(), name="auth-send-otp"),
    path("verify-otp/", VerifyOTPView.as_view(), name="auth-verify-otp"),

    path("auth/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),

    path("login/", CustomLoginView.as_view(), name="jwt-login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    path("send-reset-otp/", SendResetOTPView.as_view(), name="auth-send-reset-otp"),
    path("reset-password/", ResetPasswordView.as_view(), name="auth-reset-password"),
    
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("logout-all/", LogoutAllView.as_view(), name="auth-logout-all"),
    
    path("change-password/", ChangePasswordView.as_view(), name="auth-change-password"),

    path("social/google/", GoogleLoginView.as_view(), name="google-login"),
    path("social/microsoft/", MicrosoftAuthView.as_view()),

    path("health/", health_check),

    path("verify-mfa/", VerifyMFAView.as_view()),

    path("internal/users/by-email/", InternalUserByEmail.as_view()),
]