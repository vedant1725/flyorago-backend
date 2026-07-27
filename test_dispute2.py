import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIRequestFactory
from support.views import AdminDisputeActionView
import traceback
factory = APIRequestFactory()
request = factory.post('/api/support/admin/disputes/8/action', {'action': 'APPROVE'}, format='json')
view = AdminDisputeActionView.as_view()
try:
    response = view(request, pk=8)
    print(response.status_code, response.data)
except Exception as e:
    traceback.print_exc()
