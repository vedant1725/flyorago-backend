from django.db import models
from django.conf import settings
from trips.models import Trip

class Booking(models.Model):
    STATUS_CHOICES = (
        ('REQUEST_CREATED', 'REQUEST_CREATED'),
        ('MATCH_FOUND', 'MATCH_FOUND'),
        ('REQUEST_SENT', 'REQUEST_SENT'),
        ('REQUEST_RECEIVED', 'REQUEST_RECEIVED'),
        ('ACCEPTED', 'ACCEPTED'),
        ('PAID', 'PAID'),
        ('PARCEL_VERIFIED', 'PARCEL_VERIFIED'),
        ('IN_TRANSIT', 'IN_TRANSIT'),
        ('ARRIVED', 'ARRIVED'),
        ('OUT_FOR_DELIVERY', 'OUT_FOR_DELIVERY'),
        ('OTP_GENERATED', 'OTP_GENERATED'),
        ('DELIVERED', 'DELIVERED'),
        ('PAYMENT_RELEASED', 'PAYMENT_RELEASED'),
        ('RATED', 'RATED'),
        ('DISPUTE_OPENED', 'DISPUTE_OPENED'),
        ('DISPUTE_APPROVED', 'DISPUTE_APPROVED'),
        ('DISPUTE_REJECTED', 'DISPUTE_REJECTED'),
        ('REJECTED', 'REJECTED'),
        ('CANCELLED', 'CANCELLED'),
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
    sender_trip = models.ForeignKey(Trip, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_bookings')
    
    package_name = models.CharField(max_length=150)
    package_category = models.CharField(max_length=100)
    package_image = models.TextField(null=True, blank=True)
    
    receiver_name = models.CharField(max_length=150, null=True, blank=True)
    receiver_address = models.CharField(max_length=300, null=True, blank=True)
    receiver_phone = models.CharField(max_length=20, null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True)

    weight = models.DecimalField(max_digits=5, decimal_places=2)  # in kgs
    reward = models.DecimalField(max_digits=10, decimal_places=2)  # reward amount
    pickup_scheduled_time = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='REQUEST_CREATED')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Unpaid')
    escrow_status = models.CharField(max_length=20, null=True, blank=True) # e.g. 'Active Hold', 'Released'
    
    delivery_otp = models.CharField(max_length=6, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.delivery_otp and self.id:
            calc_otp = str((self.id * 3791 + 100000) % 900000 + 100000)
            self.delivery_otp = calc_otp
            Booking.objects.filter(pk=self.pk).update(delivery_otp=calc_otp)

    class Meta:
        indexes = [
            models.Index(fields=['sender']),
            models.Index(fields=['traveler']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Booking #{self.id} by {self.sender.email} ({self.status})"
