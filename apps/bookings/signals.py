from django.db.models.signals import post_save
from django.dispatch import receiver
from trips.models import Trip
from shipments.models import Shipment
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .services import MatchingService

@receiver(post_save, sender=Trip)
def trip_saved(sender, instance, created, **kwargs):
    if instance.status == 'Active':
        shipments = MatchingService.find_compatible_shipments_for_trip(instance.id)
        if shipments.exists():
            channel_layer = get_channel_layer()
            if channel_layer:
                # Notify the trip creator
                async_to_sync(channel_layer.group_send)(
                    f"user_{instance.user.id}_matches",
                    {
                        "type": "new_match",
                        "message": f"Found {shipments.count()} compatible shipments for your trip to {instance.to_location}."
                    }
                )
                # Notify shipment owners
                for shipment in shipments:
                    async_to_sync(channel_layer.group_send)(
                        f"user_{shipment.booking.sender.id}_matches",
                        {
                            "type": "new_match",
                            "message": f"Found a new traveller heading to {instance.to_location}!"
                        }
                    )

@receiver(post_save, sender=Shipment)
def shipment_saved(sender, instance, created, **kwargs):
    if instance.booking.status == 'Waiting Traveller':
        trips = MatchingService.find_compatible_trips_for_shipment(instance.id)
        if trips.exists():
            channel_layer = get_channel_layer()
            if channel_layer:
                # Notify the shipment owner
                async_to_sync(channel_layer.group_send)(
                    f"user_{instance.booking.sender.id}_matches",
                    {
                        "type": "new_match",
                        "message": f"Found {trips.count()} compatible travellers for your shipment."
                    }
                )
                # Notify trip owners
                for trip in trips:
                    async_to_sync(channel_layer.group_send)(
                        f"user_{trip.user.id}_matches",
                        {
                            "type": "new_match",
                            "message": f"New compatible shipment available for your trip to {trip.to_location}."
                        }
                    )
