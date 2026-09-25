from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from django.urls import include, path

from products.sitemaps import SITEMAPS


def robots(request):
    host = request.build_absolute_uri("/").rstrip("/")
    return HttpResponse(
        f"User-agent: *\nDisallow: /admin/\nDisallow: /i18n/\nDisallow: /cart/\nSitemap: {host}/sitemap.xml\n",
        content_type="text/plain",
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
    path("robots.txt", robots),
]

urlpatterns += i18n_patterns(
    path("", include("pages.urls")),
    path("", include("products.urls")),
    path("", include("orders.urls")),
    prefix_default_language=True,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
