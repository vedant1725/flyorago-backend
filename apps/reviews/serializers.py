from rest_framework import serializers
from django.db.models import Avg
from .models import Review
from profiles.models import Profile

class ReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.SerializerMethodField()
    createdAt = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ('id', 'reviewer', 'reviewed_user', 'booking', 'rating', 'comment', 'reviewer_name', 'createdAt')
        read_only_fields = ('id', 'reviewer', 'createdAt')

    def get_reviewer_name(self, obj) -> str:
        return f"{obj.reviewer.first_name} {obj.reviewer.last_name}".strip() or obj.reviewer.email.split('@')[0]

    def get_createdAt(self, obj) -> str:
        return obj.created_at.strftime('%Y-%m-%d')

class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ('booking', 'rating', 'comment')

    def validate(self, attrs):
        booking = attrs.get('booking')
        request = self.context.get('request')
        
        # Verify user belongs to booking
        if booking.sender != request.user and booking.traveler != request.user:
            raise serializers.ValidationError("You must be a participant in this booking to leave a review.")
            
        # Verify booking is completed
        if booking.status != 'Completed':
            raise serializers.ValidationError("You can only review participants of completed bookings.")
            
        return attrs
