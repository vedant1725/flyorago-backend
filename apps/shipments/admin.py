from django.contrib import admin
from .models import Shipment, ShipmentLog

class ShipmentLogInline(admin.TabularInline):
    model = ShipmentLog
    extra = 1

@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'tracking_number', 'status', 'dimensions', 'insurance', 'eta')
    list_filter = ('status', 'insurance', 'created_at')
    search_fields = ('tracking_number', 'booking__sender__email', 'booking__traveler__email')
    inlines = [ShipmentLogInline]
    ordering = ('-created_at',)

@admin.register(ShipmentLog)
class ShipmentLogAdmin(admin.ModelAdmin):
    list_display = ('shipment', 'status', 'location', 'timestamp')
    list_filter = ('status', 'timestamp')
    search_fields = ('shipment__tracking_number', 'location', 'description')
