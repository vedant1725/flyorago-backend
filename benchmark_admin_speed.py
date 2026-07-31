import os
import sys
import time
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps'))
django.setup()

from rest_framework.test import APIRequestFactory
from common.admin_views import AdminStatsView, AdminChartDataView, AdminTripsListView, AdminBookingsListView, AdminUsersListView

factory = APIRequestFactory()

def benchmark(view_cls, name, path):
    request = factory.get(path)
    view = view_cls.as_view()
    
    # Pre-warm / uncached run
    start = time.perf_counter()
    res1 = view(request)
    t1 = (time.perf_counter() - start) * 1000

    # Cached run
    start = time.perf_counter()
    res2 = view(request)
    t2 = (time.perf_counter() - start) * 1000

    print(f"[{name}] Uncached: {t1:.2f}ms | Cached: {t2:.2f}ms | Status: {res1.status_code}")

print("=" * 60)
print("BENCHMARKING ADMIN & DASHBOARD ENDPOINTS")
print("=" * 60)

benchmark(AdminStatsView, "Admin Stats View", "/api/admin/stats/")
benchmark(AdminChartDataView, "Admin Chart View (Day)", "/api/admin/chart/?period=day")
benchmark(AdminChartDataView, "Admin Chart View (Week)", "/api/admin/chart/?period=week")
benchmark(AdminChartDataView, "Admin Chart View (Month)", "/api/admin/chart/?period=month")
benchmark(AdminTripsListView, "Admin Trips List", "/api/admin/trips/")
benchmark(AdminBookingsListView, "Admin Bookings List", "/api/admin/bookings/")
benchmark(AdminUsersListView, "Admin Users List", "/api/admin/users/")

print("=" * 60)
