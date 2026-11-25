from django.urls import path
from .views import (
    UserRegisterView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    RequestOTPView,
    VerifyOTPView,
    ResetPasswordView,
    UserMeView,
    GoogleLoginView,
)

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='auth_register'),
    path("signup/", UserRegisterView.as_view(), name="auth_signup"),
    path('login/', CustomTokenObtainPairView.as_view(), name='auth_login'),
    path('refresh/', CustomTokenRefreshView.as_view(), name='auth_refresh'),
    path('google/', GoogleLoginView.as_view(), name='auth_google'),
    path('request-otp/', RequestOTPView.as_view(), name='auth_request_otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='auth_verify_otp'),
    path('reset-password/', ResetPasswordView.as_view(), name='auth_reset_password'),
    path('me/', UserMeView.as_view(), name='auth_me'),
]

