import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from vendor_app.middleware import JWTAuthMiddleware
import vendor_app.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vendor_project.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddleware(
        URLRouter(
            vendor_app.routing.websocket_urlpatterns
        )
    ),
})
