from rest_framework import serializers
from .models import Booking
from trips.models import Trip

class BookingSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    traveler_name = serializers.SerializerMethodField()
    trip_price_per_kg = serializers.SerializerMethodField()
    
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
    verification_images = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = (
            'id', 'sender_name', 'traveler_name', 'trip', 'sender_trip',
            'package_name', 'package_category', 'package_image',
            'weight', 'reward', 'trip_price_per_kg', 'status', 'payment_status', 'escrow_status', 'delivery_otp',
            'created_at', 'updated_at',
            'package', 'route', 'sender', 'traveler',
            'createdAt', 'paymentStatus', 'escrow', 'accepted_parcel_types',
            'verification_images'
        )

    def get_verification_images(self, obj) -> list:
        try:
            if hasattr(obj, 'shipment') and obj.shipment:
                images = obj.shipment.images.filter(is_verification_image=True)
                return [img.image_url for img in images if img.image_url]
        except Exception:
            pass
        return []

    def get_sender_name(self, obj) -> str:
        if obj.sender:
            return obj.sender.first_name or (obj.sender.email.split('@')[0] if obj.sender.email else 'Sender')
        return 'Sender'

    def get_traveler_name(self, obj) -> str:
        if obj.traveler:
            return obj.traveler.first_name or (obj.traveler.email.split('@')[0] if obj.traveler.email else 'Traveler')
        return 'Pending Traveler'

    def get_trip_price_per_kg(self, obj):
        if obj.trip and getattr(obj.trip, 'price_per_kg', None) is not None:
            return str(obj.trip.price_per_kg)
        return '15.00'

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
        if obj.trip and hasattr(obj.trip, 'accepted_parcel_types') and obj.trip.accepted_parcel_types:
            types = obj.trip.accepted_parcel_types
            if isinstance(types, list):
                return [t if (isinstance(t, str) and not t.startswith('data:image') and len(t) < 300) else '📦 Parcel Item' for t in types]
            return ['📦 Parcel Item']

        if obj.package_image and isinstance(obj.package_image, str):
            if not obj.package_image.startswith('data:image') and len(obj.package_image) < 300:
                return [obj.package_image]

        return ['General Items']

    def get_package(self, obj) -> dict:
        img = obj.package_image or '📦'
        if isinstance(img, str) and (img.startswith('data:image') or len(img) > 500):
            img = '📦'
        return {
            'name': obj.package_name,
            'category': obj.package_category,
            'image': img
        }

    def get_route(self, obj) -> dict:
        t = obj.trip or obj.sender_trip
        if t:
            return {
                'from': getattr(t, 'from_location', 'Unknown') or 'Unknown',
                'to': getattr(t, 'to_location', 'Unknown') or 'Unknown',
                'fromAirport': getattr(t, 'from_airport', '') or '',
                'toAirport': getattr(t, 'to_airport', '') or ''
            }
        return {'from': 'Unknown', 'to': 'Unknown', 'fromAirport': '', 'toAirport': ''}

    def get_sender(self, obj) -> dict:
        if not obj.sender:
            return {'id': '', 'name': 'Unknown', 'email': '', 'phone': '', 'kyc_status': 'NOT_SUBMITTED', 'is_kyc_verified': False, 'city': 'Sender'}
        
        try:
            profile = getattr(obj.sender, 'profile', None)
            kyc_status = profile.kyc_status if profile else 'NOT_SUBMITTED'
        except Exception:
            kyc_status = 'NOT_SUBMITTED'
        return {
            'id': str(obj.sender.id),
            'name': f"{obj.sender.first_name} {obj.sender.last_name}".strip() or (obj.sender.email.split('@')[0] if obj.sender.email else 'Sender'),
            'email': obj.sender.email or '',
            'phone': getattr(obj.sender, 'phone_number', '') or '',
            'kyc_status': kyc_status,
            'is_kyc_verified': kyc_status == 'APPROVED',
            'city': 'Sender'
        }

    def get_traveler(self, obj) -> dict:
        if not obj.traveler:
            return {
                'name': 'Pending Traveler',
                'city': 'Traveler'
            }
        return {
            'name': f"{obj.traveler.first_name} {obj.traveler.last_name}".strip() or (obj.traveler.email.split('@')[0] if obj.traveler.email else 'Traveler'),
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
            'weight', 'reward', 'receiver_name', 'receiver_phone', 'receiver_address',
            'delivery_date'
        )

    def validate(self, attrs):
        trip = attrs.get('trip')
        weight = attrs.get('weight')
        
        if trip and getattr(trip, 'available_weight', None) is not None:
            from decimal import Decimal
            if Decimal(str(trip.available_weight)) < Decimal(str(weight)):
                raise serializers.ValidationError("Booking weight exceeds trip available space allowance.")
        return attrs

class BookingActionRequestSerializer(serializers.Serializer):
    action = serializers.CharField(required=True)
    payload = serializers.JSONField(required=False, allow_null=True)

