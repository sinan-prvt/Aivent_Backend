import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chat_project.settings")

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from chat_app.middleware import JWTAuthMiddleware
import chat_app.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddleware(
        URLRouter(chat_app.routing.websocket_urlpatterns)
    ),
})