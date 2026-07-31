from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Custom claims
        token['role'] = getattr(user, 'role', 'user')
        token['email'] = user.email
        token['is_verified'] = getattr(user, 'is_verified', True)
        return token

    def validate(self, attrs):
        email = attrs.get(self.username_field, '').strip().lower()
        password = attrs.get('password', '')

        user = User.objects.filter(email__iexact=email).first()
        if user and user.check_password(password):
            if not user.is_active:
                raise serializers.ValidationError({"error_code": "ACCOUNT_BLOCKED", "detail": "Account suspended."})
            attrs[self.username_field] = user.email
            return super().validate(attrs)
        
        # Fallback to standard validation
        return super().validate(attrs)

class UserSerializer(serializers.ModelSerializer):
    kyc_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'phone_number', 'role', 'is_verified', 'kyc_status')
        read_only_fields = ('id', 'is_verified', 'kyc_status')

    def get_kyc_status(self, obj) -> str:
        from profiles.models import Profile
        try:
            profile, created = Profile.objects.get_or_create(user=obj, defaults={'kyc_status': 'APPROVED'})
            return profile.kyc_status
        except Exception:
            return 'APPROVED'

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name', 'phone_number', 'role')

    def create(self, validated_data):
        email = validated_data['email'].strip().lower()
        user = User.objects.create_user(
            email=email,
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone_number=validated_data.get('phone_number'),
            role=validated_data.get('role', 'sender'),
        )
        from profiles.models import Profile
        Profile.objects.get_or_create(user=user, defaults={'kyc_status': 'APPROVED'})
        return user

class OTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, min_length=6, max_length=6)

class RequestOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, min_length=6, max_length=6)
    new_password = serializers.CharField(required=True, min_length=8, write_only=True)
