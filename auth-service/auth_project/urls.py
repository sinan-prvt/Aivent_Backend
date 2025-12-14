from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls.static import static

schema_view = get_schema_view(
    openapi.Info(
        title="Aivent Auth API",
        default_version='v1',
    ),
    public=True,
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/auth/", include("auth_app.urls")),
    path("api/users/", include("user_app.urls")),
    
    path("admin-api/", include("auth_app.urls_admin")),
    
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
