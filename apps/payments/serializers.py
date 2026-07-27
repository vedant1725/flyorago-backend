from rest_framework import serializers
from .models import PaymentIntent, Invoice

class PaymentIntentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentIntent
        fields = ('id', 'booking', 'amount', 'payment_method', 'status', 'transaction_id', 'created_at')
        read_only_fields = ('id', 'transaction_id', 'created_at')

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ('id', 'booking', 'invoice_number', 'pdf_url', 'created_at')
        read_only_fields = ('id', 'invoice_number', 'created_at')

class PaymentIntentCreateRequestSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField(required=True)

class PaymentIntentConfirmResponseSerializer(serializers.Serializer):
    intent = PaymentIntentSerializer()
    invoice = InvoiceSerializer()

