from django.contrib import admin
from .models import PaymentIntent, Invoice

@admin.register(PaymentIntent)
class PaymentIntentAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'amount', 'payment_method', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('booking__sender__email', 'booking__traveler__email', 'transaction_id')
    ordering = ('-created_at',)

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'booking', 'created_at')
    search_fields = ('invoice_number', 'booking__sender__email')
