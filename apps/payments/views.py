from rest_framework import status, views, permissions, generics, serializers
from django.shortcuts import get_object_or_404
from django.db import transaction
from drf_spectacular.utils import extend_schema
import random

from .models import PaymentIntent, Invoice
from .serializers import (
    PaymentIntentSerializer,
    InvoiceSerializer,
    PaymentIntentCreateRequestSerializer,
    PaymentIntentConfirmResponseSerializer
)
from bookings.models import Booking
from wallet.models import Wallet, Transaction
from common.responses import success_response, failure_response

class PaymentIntentCreateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentIntentCreateRequestSerializer

    @extend_schema(request=PaymentIntentCreateRequestSerializer, responses={200: PaymentIntentSerializer})
    @transaction.atomic
    def post(self, request):
        booking_id = request.data.get('booking_id')
        booking = get_object_or_404(Booking, id=booking_id)

        # Check if booking is accepted and needs payment
        if booking.status != 'Accepted':
            return failure_response(message="Booking must be accepted before initiating payment.")

        intent = PaymentIntent.objects.create(
            booking=booking,
            amount=booking.reward,
            status='Requires Payment'
        )

        return success_response(
            data=PaymentIntentSerializer(intent).data,
            message="PaymentIntent created successfully"
        )

class PaymentIntentConfirmView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.Serializer

    @extend_schema(request=None, responses={200: PaymentIntentConfirmResponseSerializer})
    @transaction.atomic
    def post(self, request, pk):
        intent = get_object_or_404(PaymentIntent, pk=pk)
        
        if intent.status == 'Succeeded':
            return failure_response(message="This payment has already succeeded.")

        # Simulate transaction processing
        intent.status = 'Succeeded'
        intent.transaction_id = f"ch_{random.randint(10000000, 99999999)}"
        intent.save()

        # Update Booking Statuses
        booking = intent.booking
        booking.payment_status = 'Escrow Hold'
        booking.escrow_status = 'Active Hold'
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

