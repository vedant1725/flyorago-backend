import uuid
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
        # Enforce validation: Available Weight can never exceed airline allowance minus used weight
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
        ('AIRPORT_MEETING', 'AIRPORT_MEETING'),
        ('BAG_RECEIVED', 'BAG_RECEIVED'),
        ('IN_FLIGHT', 'IN_FLIGHT'),
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
        super().save(*args, **kwargs)

    def __str__(self):
        return f"LuggageBooking #{self.id} - {self.booked_weight}kg ({self.status})"


class LuggageVerificationLog(models.Model):
    VERIFICATION_TYPE_CHOICES = (
        ('QR_SCAN', 'QR_SCAN'),
        ('FACE_SELFIE', 'FACE_SELFIE'),
        ('GPS_VALIDATION', 'GPS_VALIDATION'),
        ('PASSPORT_CHECK', 'PASSPORT_CHECK'),
        ('AIRLINE_CHECK', 'AIRLINE_CHECK'),
    )

    booking = models.ForeignKey(LuggageBooking, on_delete=models.CASCADE, related_name='verification_logs')
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    verification_type = models.CharField(max_length=30, choices=VERIFICATION_TYPE_CHOICES)
    
    selfie_image = models.TextField(blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    device_hash = models.CharField(max_length=100, blank=True, null=True)
    qr_scanned_token = models.CharField(max_length=100, blank=True, null=True)
    
    is_success = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default='')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'luggage_verification_logs'
        ordering = ['-timestamp']


class LuggageWeightLog(models.Model):
    STAGE_CHOICES = (
        ('PICKUP', 'PICKUP'),
        ('AIRPORT', 'AIRPORT'),
        ('DESTINATION', 'DESTINATION'),
    )

    booking = models.ForeignKey(LuggageBooking, on_delete=models.CASCADE, related_name='weight_logs')
    logged_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES)
    weight = models.DecimalField(max_digits=6, decimal_places=2)
    photo_evidence = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, default='')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'luggage_weight_logs'
        ordering = ['-timestamp']


class LuggageRating(models.Model):
    booking = models.ForeignKey(LuggageBooking, on_delete=models.CASCADE, related_name='ratings')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='luggage_reviews_given')
    reviewee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='luggage_reviews_received')

    communication_score = models.IntegerField(default=5)
    punctuality_score = models.IntegerField(default=5)
    behaviour_score = models.IntegerField(default=5)
    accuracy_score = models.IntegerField(default=5)
    overall_rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)

    comment = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'luggage_ratings'
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
