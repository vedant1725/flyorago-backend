import os
import sys
import time
import django

sys.path.insert(0, os.path.abspath('apps'))
sys.path.insert(0, os.path.abspath('.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIRequestFactory, force_authenticate
from users.models import User
from bookings.views import BookingListCreateView
from trips.views import TripListCreateView

def run_benchmarks():
    factory = APIRequestFactory()
    user = User.objects.first()
    if not user:
        print("No user found for benchmarking.")
        return

    print("=" * 60)
    print("FLYORAGO PERFORMANCE BENCHMARK RESULTS")
    print("=" * 60)

    # 1. Test Bookings API
    req_bookings = factory.get('/api/bookings/?user_only=true')
    force_authenticate(req_bookings, user=user)
    view_bookings = BookingListCreateView.as_view()

    t0 = time.perf_counter()
    res_bookings = view_bookings(req_bookings)
    t1 = time.perf_counter()
    
    bookings_time_ms = (t1 - t0) * 1000
    bookings_size_bytes = len(str(res_bookings.data))

    print(f"1. /api/bookings/?user_only=true : {bookings_time_ms:.2f} ms | Payload Size: {bookings_size_bytes / 1024:.2f} KB")

    # 2. Test Trips API
    req_trips = factory.get('/api/trips/?user_only=true')
    force_authenticate(req_trips, user=user)
    view_trips = TripListCreateView.as_view()

    t0 = time.perf_counter()
    res_trips = view_trips(req_trips)
    t1 = time.perf_counter()

    trips_time_ms = (t1 - t0) * 1000
    trips_size_bytes = len(str(res_trips.data))

    print(f"2. /api/trips/?user_only=true    : {trips_time_ms:.2f} ms | Payload Size: {trips_size_bytes / 1024:.2f} KB")
    
    # 3. Test All Trips API
    req_all_trips = factory.get('/api/trips/')
    force_authenticate(req_all_trips, user=user)

    t0 = time.perf_counter()
    res_all_trips = view_trips(req_all_trips)
    t1 = time.perf_counter()

    all_trips_time_ms = (t1 - t0) * 1000
    all_trips_size_bytes = len(str(res_all_trips.data))

    print(f"3. /api/trips/                  : {all_trips_time_ms:.2f} ms | Payload Size: {all_trips_size_bytes / 1024:.2f} KB")
    print("=" * 60)

if __name__ == '__main__':
    run_benchmarks()
