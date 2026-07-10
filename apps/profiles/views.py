from rest_framework import status, views, permissions, generics, serializers
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_spectacular.utils import extend_schema

from .models import Profile, Address
from .serializers import (
    ProfileSerializer,
    AddressSerializer,
    KYCStatusResponseSerializer,
    KYCSubmitRequestSerializer,
    KYCAdminListResponseSerializer,
    KYCAdminActionSerializer
)
from common.responses import success_response, failure_response

User = get_user_model()

class ProfileMeView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileSerializer

    def get(self, request):
        profile, created = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile)
        return success_response(data=serializer.data, message="Profile fetched successfully")

    def patch(self, request):
        profile, created = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return success_response(data=serializer.data, message="Profile updated successfully")
        return failure_response(errors=serializer.errors, message="Failed to update profile")

class AddressListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AddressSerializer

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Addresses retrieved")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return success_response(data=serializer.data, message="Address added successfully", status_code=status.HTTP_201_CREATED)
        return failure_response(errors=serializer.errors, message="Failed to add address")

class AddressDestroyView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AddressSerializer

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return success_response(message="Address deleted successfully")

# ==========================================
# KYC ENDPOINTS (Used by KycPage and KycAdminPage)
# ==========================================

class KYCStatusView(views.APIView):
    permission_classes = [permissions.AllowAny]  # Aligning with front-end which checks status before log-in sometimes or passes userId in URL
    serializer_class = KYCStatusResponseSerializer

    @extend_schema(responses={200: KYCStatusResponseSerializer})
    def get(self, request, user_id):
        try:
            user = User.objects.filter(id=user_id).first()
            if not user:
                return failure_response(message="User not found", status_code=status.HTTP_404_NOT_FOUND)
        except Exception:
            return failure_response(message="Invalid User ID format", status_code=status.HTTP_400_BAD_REQUEST)

        profile, created = Profile.objects.get_or_create(user=user)
        data = {
            'status': profile.kyc_status,
            'rejectionReason': profile.kyc_rejection_reason or ""
        }
        return success_response(data=data, message="KYC status fetched")

class KYCSubmitView(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = KYCSubmitRequestSerializer

    @extend_schema(request=KYCSubmitRequestSerializer, responses={200: serializers.Serializer})
    def post(self, request):
        user_id = request.data.get('userId')
        if not user_id:
            return failure_response(message="userId is required", status_code=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.filter(id=user_id).first()
            if not user:
                return failure_response(message="User not found", status_code=status.HTTP_404_NOT_FOUND)
        except Exception:
            return failure_response(message="Invalid User ID format", status_code=status.HTTP_400_BAD_REQUEST)

        profile, created = Profile.objects.get_or_create(user=user)
        
        profile.kyc_document_type = request.data.get('documentType', 'national_id')
        profile.kyc_document_front = request.data.get('frontImage')
        profile.kyc_document_back = request.data.get('backImage')
        profile.kyc_selfie = request.data.get('selfieImage')
        profile.kyc_status = 'PENDING'
        profile.save()

        return success_response(message="KYC details submitted for review")

class KYCAdminListView(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = KYCAdminListResponseSerializer

    @extend_schema(responses={200: KYCAdminListResponseSerializer(many=True)})
    def get(self, request):
        # Fetch all registered users in the database
        users = User.objects.all().order_by('-date_joined')
        submissions = []
        for u in users:
            profile, created = Profile.objects.get_or_create(user=u)
            submissions.append({
                'userId': str(u.id),
                'fullName': f"{u.first_name} {u.last_name}".strip() or u.email.split('@')[0],
                'email': u.email,
                'phone': u.phone_number or "",
                'documentType': profile.kyc_document_type or "national_id",
                'frontImage': profile.kyc_document_front or "",
                'backImage': profile.kyc_document_back or "",
                'selfieImage': profile.kyc_selfie or "",
                'status': profile.kyc_status,
                'rejectionReason': profile.kyc_rejection_reason or "",
                'submittedAt': u.date_joined.isoformat() if u.date_joined else timezone.now().isoformat()
            })
        return success_response(data=submissions, message="All users and KYC profiles retrieved")

class KYCAdminActionView(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = KYCAdminActionSerializer

    @extend_schema(request=KYCAdminActionSerializer, responses={200: serializers.Serializer})
    def post(self, request):
        user_id = request.data.get('userId')
        action = request.data.get('action')
        reason = request.data.get('reason')

        if not user_id or not action:
            return failure_response(message="userId and action are required", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.filter(id=user_id).first()
            if not user:
                return failure_response(message="User not found", status_code=status.HTTP_404_NOT_FOUND)
        except Exception:
            return failure_response(message="Invalid User ID format", status_code=status.HTTP_400_BAD_REQUEST)

        profile, created = Profile.objects.get_or_create(user=user)

        if action == 'APPROVE':
            profile.kyc_status = 'APPROVED'
            profile.kyc_rejection_reason = ""
            user.is_verified = True
            user.save()
        elif action == 'REJECT':
            profile.kyc_status = 'REJECTED'
            profile.kyc_rejection_reason = reason or "Documents could not be verified."
            user.is_verified = False
            user.save()
        else:
            return failure_response(message="Invalid action. Use APPROVE or REJECT.")

        profile.save()
        return success_response(message=f"KYC submission {action.lower()}d successfully")

