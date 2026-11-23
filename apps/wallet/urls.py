from django.urls import path
from .views import (
    WalletSummaryView,
    TransactionListView,
    TransactionDetailView,
    PayoutMethodListCreateView,
    WithdrawView,
    DepositView,
    EarningsSummaryView,
    EarningsHistoryView,
    RazorpayCreateOrderView,
    RazorpayVerifyPaymentView,
)

urlpatterns = [
    path('summary', WalletSummaryView.as_view(), name='wallet_summary'),
    path('transactions', TransactionListView.as_view(), name='transaction_list'),
    path('transactions/<int:pk>', TransactionDetailView.as_view(), name='transaction_detail'),
    path('payout-methods', PayoutMethodListCreateView.as_view(), name='payout_methods'),
    path('withdraw', WithdrawView.as_view(), name='wallet_withdraw'),
    path('deposit', DepositView.as_view(), name='wallet_deposit'),
    
    # Razorpay Endpoints
    path('razorpay/create-order', RazorpayCreateOrderView.as_view(), name='razorpay_create_order'),
    path('razorpay/verify', RazorpayVerifyPaymentView.as_view(), name='razorpay_verify'),

    # Traveler Earnings
    path('earnings/summary', EarningsSummaryView.as_view(), name='earnings_summary'),
    path('earnings/history', EarningsHistoryView.as_view(), name='earnings_history'),
]
