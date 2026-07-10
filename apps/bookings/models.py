from django.db import models
from django.conf import settings
from trips.models import Trip

class Booking(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
        ('Cancelled', 'Cancelled'),
        ('In Transit', 'In Transit'),
        ('Delivered', 'Delivered'),
        ('Completed', 'Completed'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('Unpaid', 'Unpaid'),
        ('Escrow Hold', 'Escrow Hold'),
        ('Released', 'Released'),
        ('Refunded', 'Refunded'),
    )

    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sender_bookings')
    traveler = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='traveler_bookings')
    trip = models.ForeignKey(Trip, on_delete=models.SET_NULL, null=True, related_name='bookings')
    
    package_name = models.CharField(max_length=150)
    package_category = models.CharField(max_length=100)
    package_image = models.TextField(null=True, blank=True)
    
    weight = models.DecimalField(max_digits=5, decimal_places=2)  # in kgs
    reward = models.DecimalField(max_digits=10, decimal_places=2)  # reward amount
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
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
