import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client

client = Client()

endpoints = [
    '/api/admin/users/',
    '/api/admin/trips/',
    '/api/admin/stats/',
    '/api/admin/bookings/',
    '/api/admin/chart/',
    '/api/trust/admin/',
    '/api/support/admin/disputes/',
    '/api/kyc/admin/list/'
]

print("=== VERIFYING ENDPOINTS ===")
for ep in endpoints:
    response = client.get(ep)
    print(f"GET {ep.ljust(30)} -> {response.status_code}")

print("=== DONE ===")
