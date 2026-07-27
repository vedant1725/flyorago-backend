import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Collect routing patterns dynamically from apps
websocket_urlpatterns = []

try:
    from messages.routing import websocket_urlpatterns as msg_patterns
    websocket_urlpatterns.extend(msg_patterns)
except ImportError:
    pass

try:
    from notifications.routing import websocket_urlpatterns as notif_patterns
    websocket_urlpatterns.extend(notif_patterns)
except ImportError:
    pass

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
