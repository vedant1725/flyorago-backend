import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'apps')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from trips.models import Trip
from bookings.models import Booking

def sanitize_database():
    print("Starting Database Bloat Sanitization...")
    
    # 1. Clean Trip.accepted_parcel_types
    trips_updated = 0
    for trip in Trip.objects.all():
        modified = False
        raw_val = trip.accepted_parcel_types
        if raw_val:
            # If string representation contains base64 images or is > 500 chars per item
            if isinstance(raw_val, list):
                new_list = []
                for item in raw_val:
                    if isinstance(item, str) and (item.startswith('data:image') or len(item) > 500):
                        new_list.append('📦 Parcel Item')
                        modified = True
                    else:
                        new_list.append(item)
                if modified:
                    trip.accepted_parcel_types = new_list
            elif isinstance(raw_val, str) and (raw_val.startswith('data:image') or len(raw_val) > 500):
                trip.accepted_parcel_types = ['📦 Parcel Item']
                modified = True
        
        if modified:
            trip.save(update_fields=['accepted_parcel_types'])
            trips_updated += 1

    print(f"Sanitized {trips_updated} Trip records with bloated accepted_parcel_types.")

    # 2. Clean Booking.package_image
    bookings_updated = 0
    for booking in Booking.objects.all():
        raw_img = booking.package_image
        if raw_img and isinstance(raw_img, str) and len(raw_img) > 500:
            # Keep a tiny SVG/emoji placeholder or truncated string instead of 12MB raw base64 string
            booking.package_image = '📦'
            booking.save(update_fields=['package_image'])
            bookings_updated += 1

    print(f"Sanitized {bookings_updated} Booking records with bloated package_image.")
    print("Database Bloat Sanitization Complete!")

if __name__ == '__main__':
    sanitize_database()
