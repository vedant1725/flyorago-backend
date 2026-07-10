from rest_framework import generics, permissions, status
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Avg
from django.contrib.auth import get_user_model

from .models import Review
from .serializers import ReviewSerializer, ReviewCreateSerializer
from profiles.models import Profile
from common.responses import success_response, failure_response

User = get_user_model()

class ReviewListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ReviewCreateSerializer
        return ReviewSerializer

    def get_queryset(self):
        # Default to reviews received by the active user, or override via query parameter
        user_id = self.request.query_params.get('user_id')
        if user_id:
            user = get_object_or_404(User, id=user_id)
            return Review.objects.filter(reviewed_user=user)
        return Review.objects.filter(reviewed_user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Reviews list retrieved successfully")

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            booking = serializer.validated_data['booking']
            
            # The reviewed user is the other participant in the transaction
            reviewed_user = booking.traveler if booking.sender == request.user else booking.sender
            
            review = serializer.save(
                reviewer=request.user,
                reviewed_user=reviewed_user
            )

            # Update reviewed user profile stats
            profile, created = Profile.objects.get_or_create(user=reviewed_user)
            avg = Review.objects.filter(reviewed_user=reviewed_user).aggregate(avg=Avg('rating'))['avg']
            profile.rating = avg or 5.0
            profile.save()

            full_data = ReviewSerializer(review).data
            return success_response(data=full_data, message="Review submitted successfully", status_code=status.HTTP_201_CREATED)
        return failure_response(errors=serializer.errors, message="Failed to submit review")
