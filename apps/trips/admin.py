from django.contrib import admin
from .models import Trip

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'flight_number', 'airline', 'from_location', 'to_location', 'departure_date', 'status')
    list_filter = ('status', 'departure_date', 'airline')
    search_fields = ('user__email', 'flight_number', 'airline', 'from_location', 'to_location')
    ordering = ('-departure_date',)
