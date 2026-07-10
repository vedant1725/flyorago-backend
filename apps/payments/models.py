from django.db import models
from django.conf import settings
from bookings.models import Booking

class PaymentIntent(models.Model):
    STATUS_CHOICES = (
        ('Requires Payment', 'Requires Payment'),
        ('Processing', 'Processing'),
        ('Succeeded', 'Succeeded'),
        ('Refunded', 'Refunded'),
    )

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payment_intents')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=50, default='Stripe Credit Card')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Requires Payment')
    transaction_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PaymentIntent for Booking #{self.booking.id} - ${self.amount} ({self.status})"

class Invoice(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=50, unique=True)
    pdf_url = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice {self.invoice_number} (Booking #{self.booking.id})"
