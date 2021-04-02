"""
ASGI config for attendancecontrol project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/asgi/
"""

import os

import dotenv
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

import control.routing

dotenv.load_dotenv(
    # os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendancecontrol.settings.development')
if os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = os.getenv('DJANGO_SETTINGS_MODULE')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    # Just HTTP for now. (We can add other protocols later.)
    "websocket": AuthMiddlewareStack(
        URLRouter(
            control.routing.websocket_urlpatterns
        )
    ),
})
