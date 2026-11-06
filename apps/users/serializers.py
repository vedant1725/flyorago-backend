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
            profile, created = Profile.objects.get_or_create(user=obj, defaults={'kyc_status': 'NOT_SUBMITTED'})
            return profile.kyc_status
        except Exception:
            return 'NOT_SUBMITTED'

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name', 'phone_number', 'role')

    def validate_email(self, value):
        import re
        email = value.strip().lower()

        # Reject common throwaway/disposable spam domains
        disposable_domains = {
            'tempmail.com', '10minutemail.com', 'guerrillamail.com', 'throwawaymail.com',
            'mailinator.com', 'yopmail.com.trash', 'fakeinbox.com', 'trashmail.com'
        }
        domain = email.split('@')[-1] if '@' in email else ''
        if domain in disposable_domains:
            raise serializers.ValidationError("Disposable and temporary email addresses are not allowed for security reasons.")

        # Standard RFC email pattern
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, email):
            raise serializers.ValidationError("Please provide a valid official email address format.")

        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("An account with this email address already exists. Please log in.")

        return email

    def validate_phone_number(self, value):
        import re
        if not value:
            return value
        phone = re.sub(r'[\s\-\(\)]', '', str(value))
        
        # Must be valid E.164 phone format (+ followed by 8 to 15 digits)
        if not re.match(r'^\+[1-9]\d{7,14}$', phone):
            raise serializers.ValidationError("Please provide a valid international phone number in format +[country code][number] (e.g. +919876543210).")

        # Reject obvious fake numbers (all same digits like +910000000000, +911111111111)
        digits_only = re.sub(r'\D', '', phone)
        if len(set(digits_only[2:])) <= 1:
            raise serializers.ValidationError("Invalid or sequential fake mobile number detected. Please enter your real phone number.")

        if User.objects.filter(phone_number=phone).exists():
            raise serializers.ValidationError("This phone number is already registered with another account.")

        return phone

    def validate_password(self, value):
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

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
        Profile.objects.get_or_create(user=user, defaults={'kyc_status': 'NOT_SUBMITTED'})
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

    def validate_new_password(self, value):
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value
