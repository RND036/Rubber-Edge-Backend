# rubber_farm_api/asgi.py
"""
ASGI config for rubber_farm_api project.

It exposes the ASGI callable as a module-level variable named ``application``.
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from chat.middleware import JWTAuthMiddlewareStack

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rubber_farm_api.settings")

# HTTP part
django_asgi_app = get_asgi_application()

# Import websocket routing AFTER Django setup
from chat import routing as chat_routing          # noqa: E402
from events import routing as events_routing      # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTAuthMiddlewareStack(
            URLRouter(
                chat_routing.websocket_urlpatterns
                + events_routing.websocket_urlpatterns
            )
        ),
    }
)
