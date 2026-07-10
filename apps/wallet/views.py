from rest_framework import views, status, permissions, generics
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Sum
from drf_spectacular.utils import extend_schema

from .models import Wallet, Transaction, PayoutMethod
from .serializers import (
    WalletSummarySerializer,
    TransactionSerializer,
    PayoutMethodSerializer,
    WithdrawSerializer,
    DepositSerializer,
    EarningsSummaryResponseSerializer
)
from common.responses import success_response, failure_response

class WalletSummaryView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WalletSummarySerializer

    def get(self, request):
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        serializer = WalletSummarySerializer(wallet)
        return success_response(data=serializer.data, message="Wallet summary retrieved")

class TransactionListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TransactionSerializer

    def get_queryset(self):
        wallet, created = Wallet.objects.get_or_create(user=self.request.user)
        return wallet.transactions.all()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Transactions retrieved")

class TransactionDetailView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TransactionSerializer

    def get(self, request, pk):
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        tx = get_object_or_404(Transaction, pk=pk, wallet=wallet)
        serializer = TransactionSerializer(tx)
        return success_response(data=serializer.data, message="Transaction receipt fetched")

class PayoutMethodListCreateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PayoutMethodSerializer

    def get(self, request):
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        payouts = wallet.payout_methods.all()
        serializer = PayoutMethodSerializer(payouts, many=True)
        return success_response(data=serializer.data, message="Payout methods retrieved")

    def post(self, request):
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        serializer = PayoutMethodSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(wallet=wallet)
            return success_response(data=serializer.data, message="Payout method added successfully", status_code=status.HTTP_201_CREATED)
        return failure_response(errors=serializer.errors, message="Failed to add payout method")

class WithdrawView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WithdrawSerializer

    @extend_schema(request=WithdrawSerializer, responses={200: TransactionSerializer})
    @transaction.atomic
    def post(self, request):
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        serializer = WithdrawSerializer(data=request.data)
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            payout_id = serializer.validated_data['payout_method_id']
            
            payout = get_object_or_404(PayoutMethod, id=payout_id, wallet=wallet)
            
            if wallet.balance_available < amount:
                return failure_response(message="Insufficient available funds for withdrawal request")
                
            wallet.balance_available -= amount
            wallet.save()

            tx = Transaction.objects.create(
                wallet=wallet,
                amount=amount,
                type='Withdrawal',
                status='Completed',
                description=f"Withdrawal transfer to {payout.provider} ({payout.mask})"
            )
            
            return success_response(
                data=TransactionSerializer(tx).data,
                message="Withdrawal request processed successfully"
            )
        return failure_response(errors=serializer.errors, message="Invalid withdrawal parameters")

class DepositView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DepositSerializer

    @extend_schema(request=DepositSerializer, responses={200: TransactionSerializer})
    @transaction.atomic
    def post(self, request):
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        serializer = DepositSerializer(data=request.data)
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            method = serializer.validated_data['payment_method']
            
            wallet.balance_available += amount
            wallet.save()

            tx = Transaction.objects.create(
                wallet=wallet,
                amount=amount,
                type='Deposit',
                status='Completed',
                description=f"Deposit loaded via {method}"
            )
            
            return success_response(
                data=TransactionSerializer(tx).data,
                message="Deposit loaded successfully"
            )
        return failure_response(errors=serializer.errors, message="Invalid deposit parameters")

# ==========================================
# TRAVELER EARNINGS ENDPOINTS (Used by EarningsPage)
# ==========================================

class EarningsSummaryView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: EarningsSummaryResponseSerializer})
    def get(self, request):
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        
        # Calculate totals from transactions list
        total_payouts = Transaction.objects.filter(
            wallet=wallet,
            type='Withdrawal',
            status='Completed'
        ).aggregate(total=Sum('amount'))['total'] or 0.00
        
        total_received = Transaction.objects.filter(
            wallet=wallet,
            type='Payment Received',
            status='Completed'
        ).aggregate(total=Sum('amount'))['total'] or 0.00

        data = {
            'total_earnings': float(total_received),
            'monthly_earnings': float(total_received) * 0.45,  # Mock breakdown
            'pending_clearance': float(wallet.balance_pending),
            'withdrawn_total': float(total_payouts),
            # Mock graph data for frontend chart
            'charts_data': [
                {'month': 'Jan', 'amount': float(total_received) * 0.1},
                {'month': 'Feb', 'amount': float(total_received) * 0.15},
                {'month': 'Mar', 'amount': float(total_received) * 0.2},
                {'month': 'Apr', 'amount': float(total_received) * 0.25},
                {'month': 'May', 'amount': float(total_received) * 0.3},
            ]
        }
        return success_response(data=data, message="Earnings summary fetched")

class EarningsHistoryView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TransactionSerializer

    def get_queryset(self):
        wallet, created = Wallet.objects.get_or_create(user=self.request.user)
        # Earnings history typically contains payouts
        return Transaction.objects.filter(wallet=wallet, type='Withdrawal')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Withdrawal payouts list fetched")

