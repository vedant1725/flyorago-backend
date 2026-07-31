from django.db import models
from django.conf import settings

class Notification(models.Model):
    TYPE_CHOICES = (
        ('booking', 'Booking Update'),
        ('shipment', 'Shipment Log'),
        ('wallet', 'Wallet Transaction'),
        ('system', 'System Notice'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='system')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notif for {self.user.email}: {self.title} (Read: {self.is_read})"


class EmailLog(models.Model):
    STATUS_CHOICES = (
        ('QUEUED', 'Queued'),
        ('SENDING', 'Sending'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
        ('RETRYING', 'Retrying'),
        ('PREVIEW', 'Preview'),
    )

    recipient = models.EmailField(max_length=255)
    template = models.CharField(max_length=100)
    subject = models.CharField(max_length=255)
    event = models.CharField(max_length=100, default='general')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='QUEUED')
    provider = models.CharField(max_length=50, default='Resend')
    message_id = models.CharField(max_length=255, blank=True, null=True)
    idempotency_key = models.CharField(max_length=255, db_index=True, blank=True, null=True)
    error = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"EmailLog ({self.status}) -> {self.recipient} [{self.template}]"

