from rest_framework import status, views, permissions, serializers
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_spectacular.utils import extend_schema
import random
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

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        import traceback
        try:
            print("=" * 60)
            print("LOGIN DEBUG - REQUEST DATA:", request.data)
            print("LOGIN DEBUG - REQUEST KEYS:", list(request.data.keys()))

            serializer = self.get_serializer(data=request.data)

            try:
                serializer.is_valid(raise_exception=True)
            except Exception as validation_err:
                # Authentication failed (wrong email/password) or validation error
                print("LOGIN DEBUG - VALIDATION EXCEPTION TYPE:", type(validation_err).__name__)
                print("LOGIN DEBUG - VALIDATION EXCEPTION MSG:", str(validation_err))

                # Safe diagnostic: check if user exists
                try:
                    email = request.data.get('email', '')
                    diag_user = User.objects.filter(email=email).first()
                    if diag_user:
                        pw_hash = diag_user.password or ''
                        pw_prefix = pw_hash[:30] if pw_hash else 'EMPTY'
                        is_hashed = pw_hash.startswith(('pbkdf2_', 'argon2', 'bcrypt'))
                        print(f"LOGIN DEBUG - User '{email}' EXISTS, is_active={diag_user.is_active}, pw_prefix={pw_prefix}, hashed={is_hashed}")
                    else:
                        print(f"LOGIN DEBUG - User '{email}' DOES NOT EXIST in database")
                except Exception as diag_err:
                    print(f"LOGIN DEBUG - Diagnostic query failed: {diag_err}")

                # Safely get errors
                try:
                    errors = serializer.errors
                except Exception:
                    errors = {"detail": str(validation_err)}

                return failure_response(errors=errors, message="Authentication failed")

            # is_valid() succeeded — build response
            try:
                user = User.objects.filter(email=request.data.get('email')).first()
                user_dict = {}
                if user:
                    try:
                        user_dict = dict(UserSerializer(user).data)
                    except Exception as ser_err:
                        print(f"LOGIN DEBUG - UserSerializer crashed: {ser_err}")
                        user_dict = {'email': user.email}
                    user_dict['userId'] = str(user.id)
                    user_dict['fullName'] = f"{user.first_name} {user.last_name}".strip() or user.email.split('@')[0]

                data = {
                    'tokens': serializer.validated_data,
                    'user': user_dict,
                    'userId': str(user.id) if user else "",
                    'fullName': (f"{user.first_name} {user.last_name}".strip() or user.email.split('@')[0]) if user else ""
                }
                print("LOGIN DEBUG - SUCCESS for:", request.data.get('email'))
                return success_response(data=data, message="Login successful")
            except Exception as response_err:
                tb = traceback.format_exc()
                print("LOGIN DEBUG - RESPONSE BUILD ERROR:", tb)
                return failure_response(
                    errors={"detail": str(response_err)},
                    message="Login succeeded but response build failed",
                    status_code=500
                )

        except Exception as outer_e:
            tb = traceback.format_exc()
            print("LOGIN CRITICAL ERROR:", tb)
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

    @extend_schema(request=UserRegistrationSerializer, responses={201: UserSerializer})
    def post(self, request):
        import traceback
        try:
            serializer = UserRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                
                # Generate verification OTP
                otp = str(random.randint(100000, 999999))
                user.otp_code = otp
                user.otp_expires_at = timezone.now() + timedelta(minutes=10)
                user.save()

                user_dict = dict(UserSerializer(user).data)
                # In a real system, send email/sms here.
                # We add otp inside success response for easier mock testing/UI integration.
                user_dict['test_otp'] = otp
                user_dict['userId'] = str(user.id)
                user_dict['fullName'] = f"{user.first_name} {user.last_name}".strip() or user.email.split('@')[0]
                
                return success_response(
                    data=user_dict,
                    message="User registered successfully. Please verify your account with the OTP sent to your email.",
                    status_code=status.HTTP_201_CREATED
                )
            return failure_response(errors=serializer.errors, message="Registration failed")
        except Exception as outer_e:
            tb = traceback.format_exc()
            print("SIGNUP CRITICAL ERROR:", tb)
            return failure_response(errors={"detail": "Internal Server Error"}, message="Critical Signup Error", status_code=500)

class RequestOTPResponseSerializer(serializers.Serializer):
    test_otp = serializers.CharField()

class RequestOTPView(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RequestOTPSerializer

    @extend_schema(request=RequestOTPSerializer, responses={200: RequestOTPResponseSerializer})
    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.filter(email=email).first()
            if user:
                otp = str(random.randint(100000, 999999))
                user.otp_code = otp
                user.otp_expires_at = timezone.now() + timedelta(minutes=10)
                user.save()
                return success_response(data={'test_otp': otp}, message="OTP generated successfully")
            return failure_response(message="User not found", status_code=status.HTTP_404_NOT_FOUND)
        return failure_response(errors=serializer.errors, message="Invalid request data")

class VerifyOTPView(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = OTPSerializer

    @extend_schema(request=OTPSerializer, responses={200: serializers.Serializer})
    def post(self, request):
        serializer = OTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            user = User.objects.filter(email=email).first()
            if not user:
                return failure_response(message="User not found", status_code=status.HTTP_404_NOT_FOUND)
            
            if user.otp_code == otp and user.otp_expires_at > timezone.now():
                user.is_verified = True
                user.otp_code = None
                user.otp_expires_at = None
                user.save()
                return success_response(message="Account verified successfully")
            return failure_response(message="Invalid or expired OTP code")
        return failure_response(errors=serializer.errors, message="Validation error")

class ResetPasswordView(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ResetPasswordSerializer

    @extend_schema(request=ResetPasswordSerializer, responses={200: serializers.Serializer})
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            new_password = serializer.validated_data['new_password']
            user = User.objects.filter(email=email).first()
            if not user:
                return failure_response(message="User not found", status_code=status.HTTP_404_NOT_FOUND)
            
            if user.otp_code == otp and user.otp_expires_at > timezone.now():
                user.set_password(new_password)
                user.otp_code = None
                user.otp_expires_at = None
                user.save()
                return success_response(message="Password reset successfully")
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

