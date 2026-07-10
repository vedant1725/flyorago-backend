import random
import string
from django.db import models
from django.conf import settings
from bookings.models import Booking

class Shipment(models.Model):
    STATUS_CHOICES = (
        ('Package Received', 'Package Received'),
        ('In Transit', 'In Transit'),
        ('Customs Clearance', 'Customs Clearance'),
        ('Out for Handoff', 'Out for Handoff'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    )

    INSURANCE_CHOICES = (
        ('Insured ($500 limit)', 'Insured ($500 limit)'),
        ('Basic Coverage', 'Basic Coverage'),
        ('No Insurance', 'No Insurance'),
    )

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='shipment')
    tracking_number = models.CharField(max_length=50, unique=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Package Received')
    
    pickup_address = models.CharField(max_length=300)
    delivery_address = models.CharField(max_length=300)
    dimensions = models.CharField(max_length=100, default='Standard size')
    insurance = models.CharField(max_length=50, choices=INSURANCE_CHOICES, default='Basic Coverage')
    eta = models.CharField(max_length=100, default='Next 3-5 days')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['tracking_number']),
            models.Index(fields=['status']),
        ]

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            # Generate random tracking number e.g. FL-8329-US
            random_digits = ''.join(random.choices(string.digits, k=4))
            random_letters = ''.join(random.choices(string.ascii_uppercase, k=2))
            self.tracking_number = f"FL-{random_digits}-{random_letters}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Shipment for Booking #{self.booking.id} (Tracking: {self.tracking_number})"

class ShipmentLog(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='logs')
    status = models.CharField(max_length=50)
    location = models.CharField(max_length=150, null=True, blank=True)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {self.status} - {self.description}"
