import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from vendor_app.middleware import JWTAuthMiddleware
from channels.security.websocket import OriginValidator
import vendor_app.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vendor_project.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": OriginValidator(
        JWTAuthMiddleware(
            URLRouter(
                vendor_app.routing.websocket_urlpatterns
            )
        ),
        ["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5174"]
    ),
})
