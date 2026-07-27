from django.contrib import admin
from .models import Wallet, Transaction, PayoutMethod

class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    readonly_fields = ('created_at',)

class PayoutMethodInline(admin.TabularInline):
    model = PayoutMethod
    extra = 0

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance_available', 'balance_pending', 'balance_escrow', 'currency')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    inlines = [TransactionInline, PayoutMethodInline]

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'wallet', 'amount', 'type', 'status', 'created_at')
    list_filter = ('type', 'status', 'created_at')
    search_fields = ('wallet__user__email', 'description', 'reference_id')
    ordering = ('-created_at',)

@admin.register(PayoutMethod)
class PayoutMethodAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'type', 'provider', 'mask', 'is_default')
    list_filter = ('type', 'is_default')
    search_fields = ('wallet__user__email', 'provider')
