from django.db import models
from django.conf import settings
from trips.models import Trip

class Booking(models.Model):
    STATUS_CHOICES = (
        ('Draft', 'Draft'),
        ('Waiting Traveller', 'Waiting Traveller'),
        ('Booking Requested', 'Booking Requested'),
        ('Traveller Accepted', 'Traveller Accepted'),
        ('Payment Pending', 'Payment Pending'),
        ('Payment Completed', 'Payment Completed'),
        ('Pickup Scheduled', 'Pickup Scheduled'),
        ('Parcel Verification', 'Parcel Verification'),
        ('Risk Analysis', 'Risk Analysis'),
        ('Ready For Transit', 'Ready For Transit'),
        ('In Transit', 'In Transit'),
        ('Flight Landed', 'Flight Landed'),
        ('Out For Delivery', 'Out For Delivery'),
        ('Delivered', 'Delivered'),
        ('Completed', 'Completed'),
        ('Rejected', 'Rejected'),
        ('Cancelled', 'Cancelled'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('Unpaid', 'Unpaid'),
        ('Escrow Hold', 'Escrow Hold'),
        ('Released', 'Released'),
        ('Refunded', 'Refunded'),
    )

    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sender_bookings')
    traveler = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='traveler_bookings', null=True, blank=True)
    trip = models.ForeignKey(Trip, on_delete=models.SET_NULL, null=True, related_name='bookings')
    
    package_name = models.CharField(max_length=150)
    package_category = models.CharField(max_length=100)
    package_image = models.TextField(null=True, blank=True)
    
    weight = models.DecimalField(max_digits=5, decimal_places=2)  # in kgs
    reward = models.DecimalField(max_digits=10, decimal_places=2)  # reward amount
    pickup_scheduled_time = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Draft')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Unpaid')
    escrow_status = models.CharField(max_length=20, null=True, blank=True) # e.g. 'Active Hold', 'Released'
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['sender']),
            models.Index(fields=['traveler']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Booking #{self.id} by {self.sender.email} ({self.status})"
