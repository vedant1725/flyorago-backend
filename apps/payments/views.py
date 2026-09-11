from rest_framework import status, views, permissions, generics, serializers
from django.shortcuts import get_object_or_404
from django.db import transaction
from drf_spectacular.utils import extend_schema
import random

from .models import PaymentIntent, Invoice, SystemSetting
from .serializers import (
    PaymentIntentSerializer,
    InvoiceSerializer,
    PaymentIntentCreateRequestSerializer,
    PaymentIntentConfirmResponseSerializer
)
from bookings.models import Booking
from wallet.models import Wallet, Transaction
from common.responses import success_response, failure_response
from common.permissions import IsKYCApproved

class PaymentIntentCreateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated, IsKYCApproved]
    serializer_class = PaymentIntentCreateRequestSerializer

    @extend_schema(request=PaymentIntentCreateRequestSerializer, responses={200: PaymentIntentSerializer})
    @transaction.atomic
    def post(self, request):
        booking_id = request.data.get('booking_id')
        booking = get_object_or_404(Booking, id=booking_id)

        is_sender = (booking.sender == request.user)
        is_admin = (request.user.role == 'admin' or request.user.is_staff or request.user.is_superuser)
        if not is_sender and not is_admin:
            return failure_response(message="Access denied: You are not authorized to pay for this booking.", status_code=status.HTTP_403_FORBIDDEN)

        # Check if booking is accepted and needs payment
        if booking.status != 'Accepted' and booking.status != 'ACCEPTED':
            return failure_response(message="Booking must be accepted before initiating payment.")

        # Fetch dynamic platform fee setting (defaulting to 10.00 USD if not present in DB)
        from decimal import Decimal
        fee_str = SystemSetting.get_setting("platform_fee", "10.00")
        platform_fee = Decimal(fee_str)

        intent = PaymentIntent.objects.create(
            booking=booking,
            amount=booking.reward + platform_fee,
            status='Requires Payment'
        )

        return success_response(
            data=PaymentIntentSerializer(intent).data,
            message="PaymentIntent created successfully"
        )


class PaymentIntentConfirmView(views.APIView):
    permission_classes = [permissions.IsAuthenticated, IsKYCApproved]
    serializer_class = serializers.Serializer

    @extend_schema(request=None, responses={200: PaymentIntentConfirmResponseSerializer})
    @transaction.atomic
    def post(self, request, pk):
        import secrets
        intent = get_object_or_404(PaymentIntent, pk=pk)

        is_sender = (intent.booking.sender == request.user)
        is_admin = (request.user.role == 'admin' or request.user.is_staff or request.user.is_superuser)
        if not is_sender and not is_admin:
            return failure_response(message="Access denied: You are not authorized to confirm payment for this booking.", status_code=status.HTTP_403_FORBIDDEN)
        
        if intent.status == 'Succeeded':
            return failure_response(message="This payment has already succeeded.")

        # Simulate transaction processing
        intent.status = 'Succeeded'
        intent.transaction_id = f"ch_{secrets.SystemRandom().randint(10000000, 99999999)}"
        intent.save()

        # Update Booking Statuses
        booking = intent.booking
        booking.payment_status = 'Escrow Hold'
        booking.escrow_status = 'Active Hold'
        booking.status = 'PAID'  # Set status to PAID when checkout finishes
        booking.save()

        # Create wallet trace for Sender
        sender_wallet, created = Wallet.objects.get_or_create(user=booking.sender)
        sender_wallet.balance_escrow += intent.amount
        sender_wallet.save()

        Transaction.objects.create(
            wallet=sender_wallet,
            amount=intent.amount,
            type='Escrow Hold',
            status='Completed',
            description=f"Escrow deposit for cargo carried on Booking #{booking.id}",
            reference_id=str(booking.id)
        )

        # Create PaymentRecord in database for audit logs
        from .models import PaymentRecord
        from decimal import Decimal
        fee_str = SystemSetting.get_setting("platform_fee", "10.00")
        platform_fee = Decimal(fee_str)
        
        PaymentRecord.objects.create(
            user=booking.sender,
            booking=booking,
            transaction_id=intent.transaction_id,
            amount=intent.amount,
            platform_fee=platform_fee,
            status='Success'
        )

        # Create Invoice
        invoice_num = f"INV-FLY-{booking.id}-{random.randint(100, 999)}"
        invoice = Invoice.objects.create(
            booking=booking,
            invoice_number=invoice_num,
            pdf_url=f"/media/invoices/{invoice_num}.pdf"
        )

        return success_response(
            data={
                'intent': PaymentIntentSerializer(intent).data,
                'invoice': InvoiceSerializer(invoice).data
            },
            message="Payment captured and escrow hold activated"
        )

class InvoiceDetailView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InvoiceSerializer

    def get(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id)
        # Check permissions: only sender and traveler can view invoice
        if booking.sender != request.user and booking.traveler != request.user:
            return failure_response(message="Access denied", status_code=status.HTTP_403_FORBIDDEN)

        invoice = get_object_or_404(Invoice, booking=booking)
        return success_response(data=InvoiceSerializer(invoice).data, message="Invoice fetched")


class SystemSettingsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        platform_fee = SystemSetting.get_setting("platform_fee", "10.00")
        return success_response(
            data={"platform_fee": float(platform_fee)},
            message="System settings retrieved"
        )


class AdminSystemSettingsUpdateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        if not (user.is_staff or user.is_superuser or getattr(user, 'role', '') == 'admin'):
            return failure_response(message="Access denied: Admin only", status_code=status.HTTP_403_FORBIDDEN)

        platform_fee = request.data.get('platform_fee')
        if platform_fee is None:
            return failure_response(message="platform_fee is required")

        try:
            val = float(platform_fee)
            if val < 0:
                raise ValueError("Platform fee cannot be negative")
        except ValueError as e:
            return failure_response(message=str(e) or "Invalid platform_fee value")

        SystemSetting.set_setting("platform_fee", f"{val:.2f}")
        return success_response(
            data={"platform_fee": val},
            message="Platform fee updated successfully"
        )

