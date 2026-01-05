from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


def ping(request):
    return HttpResponse("CATALOG SERVICE OK")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("ping/", ping),

    # VENDOR APIs
    path("api/catalog/vendor/", include("catalog_app.urls_vendor")),

    # PUBLIC APIs
    path("api/catalog/", include("catalog_app.urls")),

    path("api/admin/catalog/", include("catalog_app.urls_admin")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
