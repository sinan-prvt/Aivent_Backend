from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include


def ping(request):
    return HttpResponse("CATALOG SERVICE OK")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("ping/", ping),

    # PUBLIC APIs
    path("api/catalog/", include("catalog_app.urls")),

    # VENDOR APIs  🔥 THIS LINE WAS MISSING
    path("api/vendor/", include("catalog_app.urls_vendor")),

    path("api/admin/catalog/", include("catalog_app.urls_admin")),
]