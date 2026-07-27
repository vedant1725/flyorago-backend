from rest_framework import serializers
from decimal import Decimal
from .models import Wallet, Transaction, PayoutMethod

class PayoutMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayoutMethod
        fields = ('id', 'type', 'provider', 'mask', 'is_default', 'created_at')
        read_only_fields = ('id', 'created_at')

class TransactionSerializer(serializers.ModelSerializer):
    createdAt = serializers.SerializerMethodField()
    refId = serializers.CharField(source='reference_id', read_only=True)

    class Meta:
        model = Transaction
        fields = ('id', 'amount', 'type', 'status', 'description', 'reference_id', 'createdAt', 'refId')

    def get_createdAt(self, obj) -> str:
        return obj.created_at.strftime('%Y-%m-%d %H:%M')

class WalletSummarySerializer(serializers.ModelSerializer):
    payout_methods = PayoutMethodSerializer(many=True, read_only=True)

    class Meta:
        model = Wallet
        fields = ('id', 'balance_available', 'balance_pending', 'balance_escrow', 'currency', 'payout_methods')

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

