import uuid
import random
from django.db import models
from django.conf import settings

class LuggageListing(models.Model):
    CABIN_CLASS_CHOICES = (
        ('Economy', 'Economy'),
        ('Premium Economy', 'Premium Economy'),
        ('Business', 'Business'),
        ('First Class', 'First Class'),
    )

    STATUS_CHOICES = (
        ('ACTIVE', 'ACTIVE'),
        ('SUSPENDED', 'SUSPENDED'),
        ('COMPLETED', 'COMPLETED'),
        ('CANCELLED', 'CANCELLED'),
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='luggage_listings'
    )
    airline = models.CharField(max_length=100)
    flight_number = models.CharField(max_length=50)
    departure_airport = models.CharField(max_length=100)
    arrival_airport = models.CharField(max_length=100)
    departure_date = models.DateField()
    departure_time = models.TimeField()
    cabin_class = models.CharField(max_length=30, choices=CABIN_CLASS_CHOICES, default='Economy')

    max_airline_allowance = models.DecimalField(max_digits=6, decimal_places=2, help_text='Max KG allowed by airline')
    currently_used_weight = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    available_weight = models.DecimalField(max_digits=6, decimal_places=2, help_text='Calculated: Max - Currently Used')

    price_per_kg = models.DecimalField(max_digits=8, decimal_places=2)
    min_kg = models.DecimalField(max_digits=6, decimal_places=2, default=1.00)
    max_kg = models.DecimalField(max_digits=6, decimal_places=2)

    accept_partial_booking = models.BooleanField(default=True)
    instant_booking = models.BooleanField(default=False)
    insurance = models.BooleanField(default=True)
    description = models.TextField(blank=True, default='')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'luggage_listings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner']),
            models.Index(fields=['status']),
            models.Index(fields=['departure_airport', 'arrival_airport']),
            models.Index(fields=['departure_date']),
        ]

    def save(self, *args, **kwargs):
        # Validation: Available Weight can never exceed airline allowance minus used weight
        calculated = self.max_airline_allowance - self.currently_used_weight
        if calculated < 0:
            calculated = 0
        self.available_weight = calculated
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Luggage #{self.id} - {self.airline} {self.flight_number} ({self.available_weight}kg free)"


class LuggageBooking(models.Model):
    STATUS_CHOICES = (
        ('REQUESTED', 'REQUESTED'),
        ('ACCEPTED', 'ACCEPTED'),
        ('PAID', 'PAID'),
        ('VERIFIED', 'VERIFIED'),
        ('VERIFICATION_REJECTED', 'VERIFICATION_REJECTED'),
        ('IN_TRANSIT', 'IN_TRANSIT'),
        ('ARRIVED', 'ARRIVED'),
        ('COMPLETED', 'COMPLETED'),
        ('REJECTED', 'REJECTED'),
        ('CANCELLED', 'CANCELLED'),
        ('DISPUTED', 'DISPUTED'),
    )

    ESCROW_STATUS_CHOICES = (
        ('PENDING', 'PENDING'),
        ('HELD', 'HELD'),
        ('RELEASED', 'RELEASED'),
        ('REFUNDED', 'REFUNDED'),
    )

    listing = models.ForeignKey(
        LuggageListing,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    booker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='luggage_bookings_as_booker'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='luggage_bookings_as_owner'
    )

    booked_weight = models.DecimalField(max_digits=6, decimal_places=2)
    price_per_kg = models.DecimalField(max_digits=8, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    insurance_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='REQUESTED')
    escrow_status = models.CharField(max_length=20, choices=ESCROW_STATUS_CHOICES, default='PENDING')

    qr_code_token = models.CharField(max_length=100, unique=True, blank=True, null=True)
    otp_code = models.CharField(max_length=6, blank=True, null=True)

    meeting_time = models.DateTimeField(null=True, blank=True)
    meeting_point = models.CharField(max_length=255, null=True, blank=True, default='Departure Terminal Main Information Desk')
    terminal = models.CharField(max_length=50, null=True, blank=True, default='T1')
    gate = models.CharField(max_length=50, null=True, blank=True, default='Gate A4')

    notes = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'luggage_bookings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booker']),
            models.Index(fields=['owner']),
            models.Index(fields=['status']),
            models.Index(fields=['qr_code_token']),
        ]

    def save(self, *args, **kwargs):
        if not self.qr_code_token:
            self.qr_code_token = f"LUG-{uuid.uuid4().hex[:12].upper()}"
        if not self.otp_code:
            self.otp_code = str(random.randint(100000, 999999))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"LuggageBooking #{self.id} - {self.booked_weight}kg ({self.status})"


class LuggageVerification(models.Model):
    booking = models.ForeignKey(LuggageBooking, on_delete=models.CASCADE, related_name='verifications')
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bag_images = models.TextField(blank=True, default='[]', help_text='JSON array of uploaded image URLs')
    weight = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True, default='')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    is_approved = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'luggage_verifications'
        ordering = ['-timestamp']


class LuggageQRLog(models.Model):
    booking = models.ForeignKey(LuggageBooking, on_delete=models.CASCADE, related_name='qr_logs')
    scanned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    qr_token = models.CharField(max_length=100)
    is_success = models.BooleanField(default=True)
    device_info = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, default='')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'luggage_qr_logs'
        ordering = ['-timestamp']


class LuggageOTPLog(models.Model):
    booking = models.ForeignKey(LuggageBooking, on_delete=models.CASCADE, related_name='otp_logs')
    entered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    otp_entered = models.CharField(max_length=6)
    is_success = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'luggage_otp_logs'
        ordering = ['-timestamp']


class LuggageTracking(models.Model):
    booking = models.ForeignKey(LuggageBooking, on_delete=models.CASCADE, related_name='tracking_logs')
    status = models.CharField(max_length=50)
    location_name = models.CharField(max_length=255, blank=True, default='')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True, default='')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'luggage_tracking'
        ordering = ['-timestamp']


class LuggageReview(models.Model):
    booking = models.ForeignKey(LuggageBooking, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='luggage_reviews_sent')
    reviewee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='luggage_reviews_got')

    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)
    behaviour_score = models.IntegerField(default=5)
    communication_score = models.IntegerField(default=5)
    timing_score = models.IntegerField(default=5)
    experience_score = models.IntegerField(default=5)

    comment = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'luggage_reviews'
        ordering = ['-created_at']


class LuggageDispute(models.Model):
    STATUS_CHOICES = (
        ('OPEN', 'OPEN'),
        ('UNDER_REVIEW', 'UNDER_REVIEW'),
        ('RESOLVED_BUYER', 'RESOLVED_BUYER'),
        ('RESOLVED_SELLER', 'RESOLVED_SELLER'),
        ('DISMISSED', 'DISMISSED'),
    )

    booking = models.ForeignKey(LuggageBooking, on_delete=models.CASCADE, related_name='disputes')
    raised_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reason = models.CharField(max_length=150)
    description = models.TextField()
    evidence_urls = models.TextField(blank=True, default='[]')

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='OPEN')
    resolution_notes = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'luggage_disputes'
        ordering = ['-created_at']
