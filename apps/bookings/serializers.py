from rest_framework import serializers
from .models import Booking
from trips.models import Trip

class BookingSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.first_name', read_only=True)
    traveler_name = serializers.CharField(source='traveler.first_name', read_only=True)
    
    # Nested fields matching the frontend interfaces
    package = serializers.SerializerMethodField()
    route = serializers.SerializerMethodField()
    sender = serializers.SerializerMethodField()
    traveler = serializers.SerializerMethodField()
    createdAt = serializers.SerializerMethodField()
    paymentStatus = serializers.CharField(source='payment_status', read_only=True)
    escrow = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = (
            'id', 'sender_name', 'traveler_name', 'trip',
            'package_name', 'package_category', 'package_image',
            'weight', 'reward', 'status', 'payment_status', 'escrow_status',
            'created_at', 'updated_at',
            'package', 'route', 'sender', 'traveler',
            'createdAt', 'paymentStatus', 'escrow'
        )

    def get_package(self, obj) -> dict:
        return {
            'name': obj.package_name,
            'category': obj.package_category,
            'image': obj.package_image or '📦'
        }

    def get_route(self, obj) -> dict:
        if obj.trip:
            return {
                'from': obj.trip.from_location,
                'to': obj.trip.to_location,
                'fromAirport': obj.trip.from_airport or '',
                'toAirport': obj.trip.to_airport or ''
            }
        return {'from': 'Unknown', 'to': 'Unknown', 'fromAirport': '', 'toAirport': ''}

    def get_sender(self, obj) -> dict:
        return {
            'name': f"{obj.sender.first_name} {obj.sender.last_name}".strip() or obj.sender.email.split('@')[0],
            'city': 'Sender'
        }

    def get_traveler(self, obj) -> dict:
        return {
            'name': f"{obj.traveler.first_name} {obj.traveler.last_name}".strip() or obj.traveler.email.split('@')[0],
            'city': 'Traveler'
        }

    def get_createdAt(self, obj) -> str:
        return obj.created_at.strftime('%Y-%m-%d')

    def get_escrow(self, obj) -> str:
        return obj.escrow_status or 'Inactive'

class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = (
            'trip', 'package_name', 'package_category', 'package_image',
            'weight', 'reward'
        )

    def validate(self, attrs):
        trip = attrs.get('trip')
        weight = attrs.get('weight')
        
        if trip.available_weight < weight:
            raise serializers.ValidationError("Booking weight exceeds trip available space allowance.")
        return attrs

class BookingActionRequestSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=['ACCEPT', 'REJECT', 'CANCEL', 'DEPOSIT_ESCROW', 'RELEASE_ESCROW'],
        required=True
    )

