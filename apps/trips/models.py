from django.db import models
from django.conf import settings

class Trip(models.Model):
    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Completed', 'Completed'),
        ('Paused', 'Paused'),
        ('Archived', 'Archived'),
        ('Cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trips')
    flight_number = models.CharField(max_length=20)
    airline = models.CharField(max_length=100)
    aircraft = models.CharField(max_length=100, null=True, blank=True)
    
    from_location = models.CharField(max_length=150)
    to_location = models.CharField(max_length=150)
    from_airport = models.CharField(max_length=150, null=True, blank=True)
    to_airport = models.CharField(max_length=150, null=True, blank=True)
    
    departure_date = models.DateField()
    departure_time = models.CharField(max_length=20)
    arrival_date = models.DateField()
    arrival_time = models.CharField(max_length=20)
    duration = models.CharField(max_length=20, default='2h')
    
    terminal_from = models.CharField(max_length=20, null=True, blank=True)
    terminal_to = models.CharField(max_length=20, null=True, blank=True)
    seats = models.CharField(max_length=20, null=True, blank=True)
    
    capacity_weight = models.DecimalField(max_digits=5, decimal_places=2, default=23.00)
    available_weight = models.DecimalField(max_digits=5, decimal_places=2, default=23.00)
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2, default=10.00)
    accepted_parcel_types = models.JSONField(default=list)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['from_location', 'to_location']),
            models.Index(fields=['departure_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.flight_number}: {self.from_location} -> {self.to_location} ({self.departure_date})"
