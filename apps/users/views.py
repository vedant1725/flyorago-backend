from rest_framework import status, views, permissions, serializers
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from drf_spectacular.utils import extend_schema
import random
import secrets
from datetime import timedelta

from .serializers import (
    UserRegistrationSerializer,
    CustomTokenObtainPairSerializer,
    OTPSerializer,
    RequestOTPSerializer,
    ResetPasswordSerializer,
    UserSerializer
)
from common.responses import success_response, failure_response
from common.audit_logging import SecurityLogger

User = get_user_model()

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'sensitive'

    def post(self, request, *args, **kwargs):
        import traceback
        ip = get_client_ip(request)
        ua = request.META.get('HTTP_USER_AGENT', 'unknown')
        try:
            print("=" * 60)
            print("LOGIN DEBUG - REQUEST DATA:", request.data)
            print("LOGIN DEBUG - REQUEST KEYS:", list(request.data.keys()))

            email = request.data.get('email', '').strip().lower()

            # ── Step 1: Check if email exists ──────────────────────────────
            try:
                diag_user = User.objects.filter(email__iexact=email).first()
            except Exception as diag_err:
                print(f"LOGIN DEBUG - Diagnostic query failed: {diag_err}")
                diag_user = None

            if not diag_user:
                print(f"LOGIN DEBUG - User '{email}' DOES NOT EXIST in database")
                SecurityLogger.log_event('LOGIN', user=None, status='FAILURE', description=f'User not found: {email}', ip_address=ip, user_agent=ua, additional_data={'email': email})
                return failure_response(
                    errors={"error_code": "EMAIL_NOT_FOUND"},
                    message="No account found with this email address. Please check your email or sign up."
                )

            # ── Step 2: Check if account is active (blocked by admin) ──────
            if not diag_user.is_active:
                print(f"LOGIN DEBUG - User '{email}' EXISTS but is BLOCKED (is_active=False)")
                SecurityLogger.log_event('LOGIN', user=diag_user, status='FAILURE', description=f'Blocked user login attempt: {email}', ip_address=ip, user_agent=ua)
                return failure_response(
                    errors={"error_code": "ACCOUNT_BLOCKED"},
                    message="Your account has been suspended by an administrator. Please contact support."
                )

            # ── Step 3: Password Verification ──────────────────────────────
            password = request.data.get('password', '')
            if not diag_user.check_password(password):
                print(f"LOGIN DEBUG - User '{email}' EXISTS but password check FAILED.")
                SecurityLogger.log_event('LOGIN', user=diag_user, status='FAILURE', description=f'Incorrect password login attempt: {email}', ip_address=ip, user_agent=ua)
                return failure_response(
                    errors={"error_code": "WRONG_PASSWORD"},
                    message="Incorrect password. Please try again.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # ── Step 4: Generate JWT Tokens & Build Response ──────────────
            try:
                from rest_framework_simplejwt.tokens import RefreshToken
                refresh = RefreshToken.for_user(diag_user)
                refresh['role'] = getattr(diag_user, 'role', 'user')
                refresh['email'] = diag_user.email
                refresh['is_verified'] = getattr(diag_user, 'is_verified', True)

                tokens = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }

                user_dict = {}
                try:
                    user_dict = dict(UserSerializer(diag_user).data)
                except Exception as ser_err:
                    print(f"LOGIN DEBUG - UserSerializer note: {ser_err}")
                    user_dict = {'email': diag_user.email}

                user_dict['userId'] = str(diag_user.id)
                user_dict['fullName'] = f"{diag_user.first_name} {diag_user.last_name}".strip() or diag_user.email.split('@')[0]

                data = {
                    'tokens': tokens,
                    'user': user_dict,
                    'userId': str(diag_user.id),
                    'fullName': user_dict['fullName']
                }
                print("LOGIN DEBUG - SUCCESS for:", diag_user.email)
                SecurityLogger.log_event('LOGIN', user=diag_user, status='SUCCESS', description=f'Login successful: {email}', ip_address=ip, user_agent=ua)
                return success_response(data=data, message="Login successful")
            except Exception as response_err:
                tb = traceback.format_exc()
                print("LOGIN DEBUG - RESPONSE BUILD ERROR:", tb)
                SecurityLogger.log_event('LOGIN', user=diag_user, status='FAILURE', description=f'Login response generation failed: {str(response_err)}', ip_address=ip, user_agent=ua)
                return failure_response(
                    errors={"detail": str(response_err)},
                    message="Login succeeded but response build failed",
                    status_code=500
                )

        except Exception as outer_e:
            tb = traceback.format_exc()
            print("LOGIN CRITICAL ERROR:", tb)
            SecurityLogger.log_event('LOGIN', user=None, status='FAILURE', description=f'Critical Login Error: {str(outer_e)}', ip_address=ip, user_agent=ua)
            return Response(
                {
                    "success": False,
                    "status": "error",
                    "message": "Critical Login Error",
                    "error": "Internal Server Error"
                },
                status=500,
            )

class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            return success_response(data=serializer.validated_data, message="Token refreshed successfully")
        except Exception as e:
            errors = serializer.errors if hasattr(serializer, '_errors') else {"detail": str(e)}
            return failure_response(errors=errors, message="Token refresh failed")

class UserRegisterView(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer
    throttle_scope = 'sensitive'

    @extend_schema(request=UserRegistrationSerializer, responses={201: UserSerializer})
    def post(self, request):
        import traceback
        ip = get_client_ip(request)
        ua = request.META.get('HTTP_USER_AGENT', 'unknown')
        try:
            serializer = UserRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                
                # Generate verification OTP
                otp = str(secrets.SystemRandom().randint(100000, 999999))
                user.otp_code = otp
                user.otp_expires_at = timezone.now() + timedelta(minutes=10)
                user.save()

                # Trigger non-blocking email notifications
                try:
                    from notifications.email_service import EmailService
                    EmailService.send_welcome(user)
                    EmailService.send_verification_otp(user, otp)
                except Exception as email_err:
                    pass

                # Generate JWT tokens for the newly registered user
                from rest_framework_simplejwt.tokens import RefreshToken
                refresh = RefreshToken.for_user(user)
                refresh['role'] = getattr(user, 'role', 'user')
                refresh['email'] = user.email
                refresh['is_verified'] = getattr(user, 'is_verified', False)

                tokens = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }

                user_dict = dict(UserSerializer(user).data)
                user_dict['tokens'] = tokens

                # In a real system, send email/sms here.
                # We add otp inside success response for easier mock testing/UI integration if in DEBUG mode.
                if settings.DEBUG:
                    user_dict['test_otp'] = otp
                user_dict['userId'] = str(user.id)
                user_dict['fullName'] = f"{user.first_name} {user.last_name}".strip() or user.email.split('@')[0]
                
                SecurityLogger.log_event('REGISTER', user=user, status='SUCCESS', description='Registration successful', ip_address=ip, user_agent=ua)
                return success_response(
                    data=user_dict,
                    message="User registered successfully. Please verify your account with the OTP sent to your email.",
                    status_code=status.HTTP_201_CREATED
                )
            SecurityLogger.log_event('REGISTER', user=None, status='FAILURE', description='Registration validation failed', ip_address=ip, user_agent=ua, additional_data=serializer.errors)
            return failure_response(errors=serializer.errors, message="Registration failed")
        except Exception as outer_e:
            tb = traceback.format_exc()
            print("SIGNUP CRITICAL ERROR:", tb)
            SecurityLogger.log_event('REGISTER', user=None, status='FAILURE', description=f'Critical registration failure: {str(outer_e)}', ip_address=ip, user_agent=ua)
            return failure_response(errors={"detail": "Internal Server Error"}, message="Critical Signup Error", status_code=500)

class RequestOTPResponseSerializer(serializers.Serializer):
    test_otp = serializers.CharField()

class RequestOTPView(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RequestOTPSerializer
    throttle_scope = 'sensitive'

    @extend_schema(request=RequestOTPSerializer, responses={200: RequestOTPResponseSerializer})
    def post(self, request):
        ip = get_client_ip(request)
        ua = request.META.get('HTTP_USER_AGENT', 'unknown')
        serializer = RequestOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.filter(email=email).first()
            if user:
                otp = str(secrets.SystemRandom().randint(100000, 999999))
                user.otp_code = otp
                user.otp_expires_at = timezone.now() + timedelta(minutes=10)
                user.save()

                try:
                    from notifications.email_service import EmailService
                    EmailService.send_verification_otp(user, otp)
                except Exception as email_err:
                    pass

                response_data = {}
                if settings.DEBUG:
                    response_data['test_otp'] = otp
                
                SecurityLogger.log_event('OTP_REQUEST', user=user, status='SUCCESS', description=f'OTP request successful: {email}', ip_address=ip, user_agent=ua)
                return success_response(data=response_data, message="OTP generated successfully")

            SecurityLogger.log_event('OTP_REQUEST', user=None, status='FAILURE', description=f'OTP requested for non-existent user: {email}', ip_address=ip, user_agent=ua)
            return failure_response(message="User not found", status_code=status.HTTP_404_NOT_FOUND)
        return failure_response(errors=serializer.errors, message="Invalid request data")

class VerifyOTPView(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = OTPSerializer
    throttle_scope = 'sensitive'

    @extend_schema(request=OTPSerializer, responses={200: serializers.Serializer})
    def post(self, request):
        ip = get_client_ip(request)
        ua = request.META.get('HTTP_USER_AGENT', 'unknown')
        serializer = OTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            user = User.objects.filter(email=email).first()
            if not user:
                SecurityLogger.log_event('OTP_VERIFY', user=None, status='FAILURE', description=f'OTP verification for non-existent user: {email}', ip_address=ip, user_agent=ua)
                return failure_response(message="User not found", status_code=status.HTTP_404_NOT_FOUND)
            
            if user.otp_code == otp and user.otp_expires_at > timezone.now():
                user.is_verified = True
                user.otp_code = None
                user.otp_expires_at = None
                user.save()
                SecurityLogger.log_event('OTP_VERIFY', user=user, status='SUCCESS', description=f'OTP verified successfully: {email}', ip_address=ip, user_agent=ua)
                return success_response(message="Account verified successfully")
            
            SecurityLogger.log_event('OTP_VERIFY', user=user, status='FAILURE', description=f'Invalid/expired OTP verification attempt: {email}', ip_address=ip, user_agent=ua)
            return failure_response(message="Invalid or expired OTP code")
        return failure_response(errors=serializer.errors, message="Validation error")

class ResetPasswordView(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ResetPasswordSerializer
    throttle_scope = 'sensitive'

    @extend_schema(request=ResetPasswordSerializer, responses={200: serializers.Serializer})
    def post(self, request):
        ip = get_client_ip(request)
        ua = request.META.get('HTTP_USER_AGENT', 'unknown')
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            new_password = serializer.validated_data['new_password']
            user = User.objects.filter(email=email).first()
            if not user:
                SecurityLogger.log_event('PASSWORD_RESET', user=None, status='FAILURE', description=f'Password reset for non-existent user: {email}', ip_address=ip, user_agent=ua)
                return failure_response(message="User not found", status_code=status.HTTP_404_NOT_FOUND)
            
            if user.otp_code == otp and user.otp_expires_at > timezone.now():
                user.set_password(new_password)
                user.otp_code = None
                user.otp_expires_at = None
                user.save()
                SecurityLogger.log_event('PASSWORD_RESET', user=user, status='SUCCESS', description=f'Password reset successful: {email}', ip_address=ip, user_agent=ua)
                return success_response(message="Password reset successfully")
            
            SecurityLogger.log_event('PASSWORD_RESET', user=user, status='FAILURE', description=f'Invalid OTP for password reset: {email}', ip_address=ip, user_agent=ua)
            return failure_response(message="Invalid or expired OTP code")
        return failure_response(errors=serializer.errors, message="Validation error")

class UserMeView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request):
        serializer = UserSerializer(request.user)
        return success_response(data=serializer.data, message="User profile fetched")

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return success_response(data=serializer.data, message="User profile updated")
        return failure_response(errors=serializer.errors, message="Failed to update profile")

