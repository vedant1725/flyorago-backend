from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'traveler', 'package_name', 'weight', 'reward', 'status', 'payment_status')
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('sender__email', 'traveler__email', 'package_name')
    ordering = ('-created_at',)
