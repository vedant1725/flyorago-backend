from django.db import models
from django.conf import settings

class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance_available = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    balance_pending = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    balance_escrow = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=10, default='USD')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wallet of {self.user.email} (Avail: ${self.balance_available})"

class Transaction(models.Model):
    TYPE_CHOICES = (
        ('Deposit', 'Deposit'),
        ('Withdrawal', 'Withdrawal'),
        ('Payment Sent', 'Payment Sent'),
        ('Payment Received', 'Payment Received'),
        ('Refund', 'Refund'),
        ('Escrow Hold', 'Escrow Hold'),
        ('Escrow Release', 'Escrow Release'),
    )

    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    )

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    
    description = models.TextField(blank=True)
    reference_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Tx #{self.id} - {self.type} of ${self.amount} ({self.status})"

class PayoutMethod(models.Model):
    TYPE_CHOICES = (
        ('bank_account', 'Bank Account'),
        ('paypal', 'PayPal Account'),
        ('card', 'Credit/Debit Card'),
    )

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='payout_methods')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='bank_account')
    provider = models.CharField(max_length=100) # e.g. Chase Bank, Paypal Inc.
    mask = models.CharField(max_length=50) # e.g. **** 1234
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} ({self.mask}) for {self.wallet.user.email}"
