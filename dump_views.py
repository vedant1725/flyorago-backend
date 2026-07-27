import os
import django
import inspect
from rest_framework.views import APIView
import importlib

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

apps = ['users', 'profiles', 'trips', 'bookings', 'shipments', 'wallet', 'payments', 'pickups', 'chat', 'notifications', 'reviews', 'support', 'flights']

for app in apps:
    try:
        module = importlib.import_module(f'apps.{app}.views')
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, APIView) and obj.__module__.startswith('apps.'):
                print(f"{app.ljust(15)} : {name}")
    except Exception as e:
        print(f"Error loading {app}: {e}")
