from rest_framework import serializers
from decimal import Decimal
from django.db import models
from .models import Wallet, Transaction, PayoutMethod

class PayoutMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayoutMethod
        fields = ('id', 'type', 'provider', 'mask', 'is_default', 'created_at')
        read_only_fields = ('id', 'created_at')

class TransactionSerializer(serializers.ModelSerializer):
    createdAt = serializers.SerializerMethodField()
    refId = serializers.CharField(source='reference_id', read_only=True)
    counterparty = serializers.SerializerMethodField()
    booking_details = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = ('id', 'amount', 'type', 'status', 'description', 'reference_id', 'createdAt', 'refId', 'counterparty', 'booking_details')

    def get_createdAt(self, obj) -> str:
        return obj.created_at.strftime('%Y-%m-%d %H:%M')

    def _resolve_booking_and_parties(self, obj):
        if hasattr(obj, '_cached_tx_meta'):
            return obj._cached_tx_meta

        meta = {'counterparty': None, 'booking': None}
        ref = (obj.reference_id or '').strip()
        user = obj.wallet.user

        from bookings.models import Booking
        from luggage_sharing.models import LuggageBooking

        booking_obj = None
        luggage_obj = None

        if ref.startswith('FEE-') or 'Platform Service Fee' in obj.description:
            # Platform Fee transaction
            import re
            m = re.search(r'\d+', ref) or re.search(r'Booking #(\d+)', obj.description)
            if m:
                booking_obj = Booking.objects.filter(id=int(m.group(1) if m.groups() else m.group())).select_related('sender', 'traveler', 'trip').first()

            meta['counterparty'] = {
                'name': 'Flyorago Platform (Admin)',
                'email': 'billing@flyorago.com',
                'phone': '+91 Platform Support',
                'role': 'Platform Service',
                'is_sender': False
            }
        elif ref.startswith('LUG-') or 'Luggage' in obj.description:
            # Luggage sharing reference
            import re
            m = re.search(r'\d+', ref)
            if m:
                luggage_obj = LuggageBooking.objects.filter(id=int(m.group())).select_related('booker', 'owner', 'listing').first()
        elif ref.isdigit():
            booking_obj = Booking.objects.filter(id=int(ref)).select_related('sender', 'traveler', 'trip').first()
        else:
            # Check description for Booking #ID
            import re
            m = re.search(r'Booking #(\d+)', obj.description)
            if m:
                booking_obj = Booking.objects.filter(id=int(m.group(1))).select_related('sender', 'traveler', 'trip').first()

        if booking_obj:
            is_sender = (user.id == booking_obj.sender_id)
            other_user = booking_obj.traveler if is_sender else booking_obj.sender
            
            counterparty_name = "Not Assigned"
            counterparty_email = ""
            counterparty_phone = ""
            counterparty_role = "Traveler" if is_sender else "Sender"

            if other_user:
                full_name = f"{other_user.first_name} {other_user.last_name}".strip()
                counterparty_name = full_name if full_name else other_user.email.split('@')[0]
                counterparty_email = other_user.email
                counterparty_phone = getattr(other_user, 'phone_number', '') or ''

            meta['counterparty'] = {
                'name': counterparty_name,
                'email': counterparty_email,
                'phone': counterparty_phone,
                'role': counterparty_role,
                'is_sender': is_sender
            }

            trip_route = ""
            if booking_obj.trip:
                trip_route = f"{booking_obj.trip.from_location} → {booking_obj.trip.to_location}"
            elif booking_obj.sender_trip:
                trip_route = f"{booking_obj.sender_trip.from_location} → {booking_obj.sender_trip.to_location}"

            meta['booking'] = {
                'id': booking_obj.id,
                'type': 'Parcel Delivery',
                'package_name': booking_obj.package_name,
                'package_category': booking_obj.package_category,
                'weight': f"{booking_obj.weight} kg" if booking_obj.weight else None,
                'reward': str(booking_obj.reward),
                'route': trip_route,
                'status': booking_obj.status,
                'receiver_name': booking_obj.receiver_name,
                'receiver_address': booking_obj.receiver_address
            }

        elif luggage_obj:
            is_booker = (user.id == luggage_obj.booker_id)
            other_user = luggage_obj.owner if is_booker else luggage_obj.booker
            
            counterparty_name = "Not Assigned"
            counterparty_email = ""
            counterparty_role = "Luggage Owner / Traveler" if is_booker else "Sender / Booker"

            if other_user:
                full_name = f"{other_user.first_name} {other_user.last_name}".strip()
                counterparty_name = full_name if full_name else other_user.email.split('@')[0]
                counterparty_email = other_user.email

            meta['counterparty'] = {
                'name': counterparty_name,
                'email': counterparty_email,
                'role': counterparty_role,
                'is_sender': is_booker
            }

            route_str = ""
            if luggage_obj.listing:
                route_str = f"{luggage_obj.listing.departure_airport} → {luggage_obj.listing.arrival_airport}"

            meta['booking'] = {
                'id': luggage_obj.id,
                'type': 'Luggage Sharing',
                'booked_weight': f"{luggage_obj.booked_weight} kg",
                'total_price': str(luggage_obj.total_price),
                'route': route_str,
                'status': luggage_obj.status,
                'terminal': luggage_obj.terminal,
                'meeting_point': luggage_obj.meeting_point
            }

        obj._cached_tx_meta = meta
        return meta

    def get_counterparty(self, obj):
        return self._resolve_booking_and_parties(obj)['counterparty']

    def get_booking_details(self, obj):
        return self._resolve_booking_and_parties(obj)['booking']

class WalletSummarySerializer(serializers.ModelSerializer):
    payout_methods = PayoutMethodSerializer(many=True, read_only=True)
    total_earnings = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = ('id', 'balance_available', 'balance_pending', 'balance_escrow', 'currency', 'total_earnings', 'payout_methods')

    def get_total_earnings(self, obj) -> float:
        """
        Calculate actual lifetime earnings for Traveler rewards.
        Sender payments into escrow or deposits do NOT count as earnings.
        Only completed 'Escrow Release' or 'Payment Received' from completed deliveries count.
        Minus any platform fee deductions from rewards.
        """
        gross_received = obj.transactions.filter(
            type__in=['Escrow Release', 'Payment Received'],
            status='Completed'
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

        fee_deducted = obj.transactions.filter(
            type='Withdrawal',
            description__icontains='Platform Service Fee deducted from reward',
            status='Completed'
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

        net_earnings = max(Decimal('0.00'), gross_received - fee_deducted)
        return float(net_earnings)

class WithdrawSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('5.00'))
    payout_method_id = serializers.IntegerField(required=True)

class DepositSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('5.00'))
    payment_method = serializers.CharField(required=True) # e.g. Visa, Mastercard, Paypal

# Serializers for OpenAPI documentation only
class ChartDataPointSerializer(serializers.Serializer):
    month = serializers.CharField()
    amount = serializers.FloatField()

class EarningsSummaryResponseSerializer(serializers.Serializer):
    total_earnings = serializers.FloatField()
    monthly_earnings = serializers.FloatField()
    pending_clearance = serializers.FloatField()
    withdrawn_total = serializers.FloatField()
    charts_data = ChartDataPointSerializer(many=True)

