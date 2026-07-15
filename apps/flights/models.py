import uuid
from django.db import models
from django.utils import timezone

class Flight(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Core Identification
    flight_number = models.CharField(max_length=20, db_index=True)
    travel_date = models.DateField(db_index=True)
    
    # Airline Information
    call_sign = models.CharField(max_length=20, blank=True, null=True)
    airline_name = models.CharField(max_length=100, blank=True, null=True)
    airline_iata = models.CharField(max_length=10, blank=True, null=True)
    airline_icao = models.CharField(max_length=10, blank=True, null=True)
    
    # Aircraft Information
    aircraft_model = models.CharField(max_length=100, blank=True, null=True)
    aircraft_registration = models.CharField(max_length=20, blank=True, null=True)
    aircraft_modes = models.CharField(max_length=20, blank=True, null=True)
    
    # Status
    flight_status = models.CharField(max_length=50, blank=True, null=True)
    cargo_status = models.CharField(max_length=50, blank=True, null=True)
    codeshare_status = models.CharField(max_length=50, blank=True, null=True)
    
    # Distance
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    distance_miles = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Departure Airport
    departure_airport_name = models.CharField(max_length=150, blank=True, null=True)
    departure_airport_short_name = models.CharField(max_length=100, blank=True, null=True)
    departure_municipality = models.CharField(max_length=100, blank=True, null=True)
    departure_country = models.CharField(max_length=100, blank=True, null=True)
    departure_icao = models.CharField(max_length=10, blank=True, null=True)
    departure_iata = models.CharField(max_length=10, blank=True, null=True)
    departure_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    departure_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    departure_timezone = models.CharField(max_length=50, blank=True, null=True)
    
    # Departure Times & Info
    departure_scheduled_utc = models.DateTimeField(blank=True, null=True)
    departure_scheduled_local = models.DateTimeField(blank=True, null=True)
    departure_revised_utc = models.DateTimeField(blank=True, null=True)
    departure_revised_local = models.DateTimeField(blank=True, null=True)
    departure_runway_time = models.DateTimeField(blank=True, null=True)
    departure_terminal = models.CharField(max_length=20, blank=True, null=True)
    
    # Arrival Airport
    arrival_airport_name = models.CharField(max_length=150, blank=True, null=True)
    arrival_short_name = models.CharField(max_length=100, blank=True, null=True)
    arrival_municipality = models.CharField(max_length=100, blank=True, null=True)
    arrival_country = models.CharField(max_length=100, blank=True, null=True)
    arrival_icao = models.CharField(max_length=10, blank=True, null=True)
    arrival_iata = models.CharField(max_length=10, blank=True, null=True)
    arrival_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    arrival_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    arrival_timezone = models.CharField(max_length=50, blank=True, null=True)
    
    # Arrival Times & Info
    arrival_scheduled_utc = models.DateTimeField(blank=True, null=True)
    arrival_scheduled_local = models.DateTimeField(blank=True, null=True)
    arrival_revised_utc = models.DateTimeField(blank=True, null=True)
    arrival_revised_local = models.DateTimeField(blank=True, null=True)
    arrival_runway_time = models.DateTimeField(blank=True, null=True)
    arrival_runway = models.CharField(max_length=20, blank=True, null=True)
    
    # System
    last_updated_utc = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'flights_flight'
        ordering = ['-departure_scheduled_utc']
        constraints = [
            models.UniqueConstraint(fields=['flight_number', 'travel_date'], name='unique_flight_date')
        ]

    def __str__(self):
        return f"{self.flight_number} on {self.travel_date}"
