from rest_framework import serializers
from .models import Profile, Address

class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)

    class Meta:
        model = Profile
        fields = (
            'id', 'email', 'first_name', 'last_name', 'phone_number',
            'avatar', 'bio', 'languages', 'emergency_contact',
            'pref_fragile', 'pref_electronics', 'pref_documents', 'pref_liquid',
            'kyc_status', 'kyc_rejection_reason', 'level', 'completed_trips', 'rating'
        )
        read_only_fields = ('id', 'kyc_status', 'kyc_rejection_reason', 'level', 'completed_trips', 'rating')

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ('id', 'tag', 'text', 'created_at')
        read_only_fields = ('id', 'created_at')

class KYCSubmitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('kyc_document_type', 'kyc_document_front', 'kyc_document_back', 'kyc_selfie')
        extra_kwargs = {
            'kyc_document_front': {'required': True},
            'kyc_selfie': {'required': True},
        }

class KYCReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[('APPROVED', 'Approved'), ('REJECTED', 'Rejected')])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)

# Documentation helper serializers
class KYCStatusResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    rejectionReason = serializers.CharField(allow_blank=True)

class KYCSubmitRequestSerializer(serializers.Serializer):
    userId = serializers.CharField(required=True)
    documentType = serializers.CharField(required=False, default='national_id')
    frontImage = serializers.CharField(required=True)
    backImage = serializers.CharField(required=False, allow_blank=True)
    selfieImage = serializers.CharField(required=True)

class KYCAdminListResponseSerializer(serializers.Serializer):
    userId = serializers.CharField()
    fullName = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField(allow_blank=True)
    documentType = serializers.CharField()
    frontImage = serializers.CharField(allow_blank=True)
    backImage = serializers.CharField(allow_blank=True)
    selfieImage = serializers.CharField(allow_blank=True)
    status = serializers.CharField()
    rejectionReason = serializers.CharField(allow_blank=True)
    submittedAt = serializers.CharField()

class KYCAdminActionSerializer(serializers.Serializer):
    userId = serializers.CharField(required=True)
    action = serializers.ChoiceField(choices=['APPROVE', 'REJECT'], required=True)
    reason = serializers.CharField(required=False, allow_blank=True)

