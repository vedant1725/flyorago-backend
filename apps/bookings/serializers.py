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
    accepted_parcel_types = serializers.SerializerMethodField()
    delivery_otp = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = (
            'id', 'sender_name', 'traveler_name', 'trip', 'sender_trip',
            'package_name', 'package_category', 'package_image',
            'weight', 'reward', 'status', 'payment_status', 'escrow_status', 'delivery_otp',
            'created_at', 'updated_at',
            'package', 'route', 'sender', 'traveler',
            'createdAt', 'paymentStatus', 'escrow', 'accepted_parcel_types'
        )

    def get_delivery_otp(self, obj) -> str:
        try:
            if getattr(obj, 'delivery_otp', None):
                return str(obj.delivery_otp)
            if getattr(obj, 'id', None):
                return str((obj.id * 3791 + 100000) % 900000 + 100000)
            return '123456'
        except Exception:
            return '123456'

    def get_accepted_parcel_types(self, obj) -> list:
        import json
        if obj.package_image:
            try:
                parsed = json.loads(obj.package_image)
                if isinstance(parsed, list) and len(parsed) > 0:
                    return parsed
            except Exception:
                pass
            if isinstance(obj.package_image, str) and len(obj.package_image) > 30:
                return [obj.package_image]

        # Look up Sender's SENDER_REQUEST trip for uploaded images
        if obj.sender:
            try:
                sender_trips = Trip.objects.filter(user=obj.sender, airline='SENDER_REQUEST').order_by('-created_at')
                for st in sender_trips:
                    if st.accepted_parcel_types and isinstance(st.accepted_parcel_types, list) and len(st.accepted_parcel_types) > 0:
                        return st.accepted_parcel_types
            except Exception:
                pass

        if obj.trip and hasattr(obj.trip, 'accepted_parcel_types') and obj.trip.accepted_parcel_types:
            return obj.trip.accepted_parcel_types

        return []

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
        from profiles.models import Profile
        profile = Profile.objects.filter(user=obj.sender).first()
        kyc_status = profile.kyc_status if profile else 'NOT_SUBMITTED'
        return {
            'id': str(obj.sender.id),
            'name': f"{obj.sender.first_name} {obj.sender.last_name}".strip() or obj.sender.email.split('@')[0],
            'email': obj.sender.email,
            'phone': getattr(obj.sender, 'phone_number', '') or (profile.phone_number if profile else ''),
            'kyc_status': kyc_status,
            'is_kyc_verified': kyc_status == 'APPROVED',
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
            'trip', 'sender_trip', 'package_name', 'package_category', 'package_image',
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
        choices=[
            'ACCEPT', 'REJECT', 'CANCEL', 
            'MARK_PAYMENT_COMPLETED', 'DEPOSIT_ESCROW',
            'SCHEDULE_PICKUP',
            'VERIFY_PARCEL',
            'START_TRANSIT',
            'FLIGHT_LANDED',
            'OUT_FOR_DELIVERY',
            'CONFIRM_DELIVERY', 'RELEASE_ESCROW'
        ],
        required=True
    )
    payload = serializers.JSONField(required=False, allow_null=True)

