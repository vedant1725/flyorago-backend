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
    receiver = serializers.SerializerMethodField()
    createdAt = serializers.SerializerMethodField()
    paymentStatus = serializers.CharField(source='payment_status', read_only=True)
    escrow = serializers.SerializerMethodField()
    accepted_parcel_types = serializers.SerializerMethodField()
    delivery_otp = serializers.SerializerMethodField()
    delivery_qr_code = serializers.SerializerMethodField()
    verification_images = serializers.SerializerMethodField()
    trip_details = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = (
            'id', 'sender_name', 'traveler_name', 'trip', 'sender_trip',
            'package_name', 'package_category', 'package_image',
            'receiver_name', 'receiver_address', 'receiver_phone', 'delivery_date',
            'weight', 'reward', 'trip_price_per_kg', 'status', 'payment_status', 'escrow_status', 'delivery_otp', 'delivery_qr_code',
            'created_at', 'updated_at',
            'package', 'route', 'sender', 'traveler', 'receiver',
            'createdAt', 'paymentStatus', 'escrow', 'accepted_parcel_types',
            'verification_images', 'trip_details'
        )

    def get_trip_details(self, obj) -> dict:
        if not obj.trip:
            return None
        return {
            'id': obj.trip.id,
            'flight_number': obj.trip.flight_number,
            'airline': obj.trip.airline,
            'departure_date': str(obj.trip.departure_date) if obj.trip.departure_date else '',
            'departure_time': obj.trip.departure_time,
            'from_location': obj.trip.from_location,
            'to_location': obj.trip.to_location,
            'available_weight': str(obj.trip.available_weight),
            'price_per_kg': str(obj.trip.price_per_kg),
        }

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

    def get_delivery_qr_code(self, obj) -> str:
        """
        Generates actual Base64 Data-URI PNG QR Code from backend.
        Encodes FLYORA-DELIVERY:<bookingId>:<otp> for instant verification upon camera scanning.
        """
        try:
            import qrcode, io, base64
            otp = self.get_delivery_otp(obj)
            booking_id = obj.id if getattr(obj, 'id', None) else 1
            payload = f"FLYORA-DELIVERY:{booking_id}:{otp}"

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=8,
                border=2,
            )
            qr.add_data(payload)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return f"data:image/png;base64,{b64}"
        except Exception as e:
            return ""

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
            return {'id': '', 'name': 'Not Assigned Yet', 'email': '', 'city': 'Traveler'}
        from profiles.models import Profile
        traveler_profile = Profile.objects.filter(user=obj.traveler).first()
        kyc_status = traveler_profile.kyc_status if traveler_profile else 'NOT_SUBMITTED'
        
        trip_obj = obj.trip
        return {
            'id': str(obj.traveler.id),
            'name': f"{obj.traveler.first_name} {obj.traveler.last_name}".strip() or (obj.traveler.email.split('@')[0] if obj.traveler.email else 'Traveler'),
            'email': obj.traveler.email or '',
            'phone': getattr(obj.traveler, 'phone_number', '') or '',
            'flightNo': trip_obj.flight_number if trip_obj else 'FL-782',
            'airline': trip_obj.airline if trip_obj else 'Commercial Airline',
            'departureDate': str(trip_obj.departure_date) if (trip_obj and trip_obj.departure_date) else '',
            'departureTime': trip_obj.departure_time if trip_obj else '12:00:00',
            'kyc_status': kyc_status,
            'is_kyc_verified': kyc_status == 'APPROVED',
            'rating': float(getattr(obj.traveler, 'rating', 4.9) or 4.9),
            'avatar': getattr(traveler_profile, 'avatar_url', None) if traveler_profile else None,
            'city': (getattr(traveler_profile, 'city', None) or (trip_obj.from_location if trip_obj else 'Traveler'))
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
        
        if trip and getattr(trip, 'available_weight', None) is not None:
            from decimal import Decimal
            if Decimal(str(trip.available_weight)) < Decimal(str(weight)):
                raise serializers.ValidationError("Booking weight exceeds trip available space allowance.")
        return attrs

class BookingActionRequestSerializer(serializers.Serializer):
    action = serializers.CharField(required=True)
    payload = serializers.JSONField(required=False, allow_null=True)

