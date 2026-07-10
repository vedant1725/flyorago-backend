import os
from django.core.wsgi import get_wsgi_application
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()

try:
    print("=" * 60)
    print("RUNNING AUTOMATIC MIGRATIONS ON STARTUP...")
    call_command('migrate', interactive=False)
    print("AUTOMATIC MIGRATIONS SUCCESSFUL!")
    print("=" * 60)
except Exception as e:
    print(f"AUTOMATIC MIGRATIONS FAILED: {e}")
