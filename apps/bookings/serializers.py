from rest_framework import serializers
from .models import Booking
from trips.models import Trip

class BookingSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.first_name', read_only=True)
    traveler_name = serializers.CharField(source='traveler.first_name', read_only=True)
    trip_price_per_kg = serializers.DecimalField(source='trip.price_per_kg', max_digits=10, decimal_places=2, read_only=True)
    
    # Nested fields matching the frontend interfaces
    package = serializers.SerializerMethodField()
    route = serializers.SerializerMethodField()
    sender = serializers.SerializerMethodField()
    traveler = serializers.SerializerMethodField()
    receiver = serializers.SerializerMethodField()
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
            'receiver_name', 'receiver_address', 'receiver_phone', 'delivery_date',
            'weight', 'reward', 'trip_price_per_kg', 'status', 'payment_status', 'escrow_status', 'delivery_otp',
            'created_at', 'updated_at',
            'package', 'route', 'sender', 'traveler', 'receiver',
            'createdAt', 'paymentStatus', 'escrow', 'accepted_parcel_types'
        )

    def get_receiver(self, obj) -> dict:
        name = (obj.receiver_name or '').strip()
        phone = (obj.receiver_phone or '').strip()
        address = (obj.receiver_address or '').strip()

        # Check sender_trip fallback if any field is missing
        if obj.sender_trip:
            if not name and obj.sender_trip.terminal_from and obj.sender_trip.terminal_from != 'N/A':
                name = obj.sender_trip.terminal_from.strip()
            if not phone and obj.sender_trip.terminal_to and obj.sender_trip.terminal_to != 'N/A':
                phone = obj.sender_trip.terminal_to.strip()
            if not address and obj.sender_trip.to_location:
                address = obj.sender_trip.to_location.strip()
            if obj.sender_trip.notes:
                try:
                    import json
                    data = json.loads(obj.sender_trip.notes)
                    if isinstance(data, dict):
                        if not name:
                            name = (data.get('receiver_name') or data.get('receiverName') or '').strip()
                        if not phone:
                            phone = (data.get('receiver_phone') or data.get('receiverPhone') or '').strip()
                        if not address:
                            address = (data.get('receiver_address') or data.get('receiverAddress') or '').strip()
                except Exception:
                    pass

        return {
            'name': name or (f"{obj.sender.first_name}'s Contact" if (obj.sender and obj.sender.first_name) else 'Designated Receiver'),
            'phone': phone,
            'address': address or (obj.trip.to_location if obj.trip else 'Destination Point')
        }

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
        if obj.trip:
            return {
                'from': obj.trip.from_location,
                'to': obj.trip.to_location,
                'fromAirport': obj.trip.from_airport or '',
                'toAirport': obj.trip.to_airport or ''
            }
        if hasattr(obj, 'shipment') and obj.shipment:
            return {
                'from': obj.shipment.pickup_address or 'Origin',
                'to': obj.shipment.delivery_address or 'Destination',
                'fromAirport': '',
                'toAirport': ''
            }
        return {'from': 'Origin', 'to': 'Destination', 'fromAirport': '', 'toAirport': ''}

    def get_sender(self, obj) -> dict:
        if not obj.sender:
            return {'id': '', 'name': 'Unknown', 'email': '', 'phone': '', 'kyc_status': 'NOT_SUBMITTED', 'is_kyc_verified': False, 'city': 'Sender'}
        
        # Use prefetched profile or safe lookup
        profile = getattr(obj.sender, 'profile', None)
        kyc_status = profile.kyc_status if profile else 'NOT_SUBMITTED'
        return {
            'id': str(obj.sender.id),
            'name': f"{obj.sender.first_name} {obj.sender.last_name}".strip() or obj.sender.email.split('@')[0],
            'email': obj.sender.email,
            'phone': getattr(obj.sender, 'phone_number', '') or '',
            'kyc_status': kyc_status,
            'is_kyc_verified': kyc_status == 'APPROVED',
            'city': 'Sender'
        }


    def get_traveler(self, obj) -> dict:
        if not obj.traveler:
            return {'id': '', 'name': 'Not Assigned Yet', 'email': '', 'city': 'Traveler'}
        return {
            'id': str(obj.traveler.id),
            'name': f"{obj.traveler.first_name} {obj.traveler.last_name}".strip() or obj.traveler.email.split('@')[0],
            'email': obj.traveler.email,
            'city': 'Traveler'
        }

    def get_createdAt(self, obj) -> str:
        return obj.created_at.strftime('%Y-%m-%d')

    def get_escrow(self, obj) -> str:
        return obj.escrow_status or 'Inactive'

class BookingCreateSerializer(serializers.ModelSerializer):
    trip = serializers.PrimaryKeyRelatedField(queryset=Trip.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Booking
        fields = (
            'trip', 'sender_trip', 'package_name', 'package_category', 'package_image',
            'receiver_name', 'receiver_address', 'receiver_phone', 'delivery_date',
            'weight', 'reward'
        )

    def validate(self, attrs):
        trip = attrs.get('trip')
        weight = attrs.get('weight')
        
        if trip and trip.available_weight < weight:
            raise serializers.ValidationError("Booking weight exceeds trip available space allowance.")
        return attrs

class BookingActionRequestSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=[
            'ACCEPT', 'Accept', 'REJECT', 'Reject', 'CANCEL', 'PAY', 'ARRIVED', 'IN_TRANSIT', 
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

