from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path
from django.views import defaults as default_views
from django.views.generic import TemplateView


def home(request):
    if request.get_host() == "wbmissingfound.com":
        return redirect("https://www.wbmissingfound.com/")
    else:
        return TemplateView.as_view(template_name="pages/home.html")(request)


urlpatterns = [
    path("", home, name="home"),
    path(
        "about/", TemplateView.as_view(template_name="pages/about.html"), name="about"
    ),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path(
        "users/",
        include(
            "missing_persons_match_unidentified_dead_bodies.users.urls",
            namespace="users",
        ),
    ),
    path("accounts/", include("allauth.urls")),
    # Your stuff: custom urls includes go here
    path(
        "backend/",
        include(
            "missing_persons_match_unidentified_dead_bodies.backend.urls",
            namespace="backend",
        ),
    ),
    path(
        "ajax/",
        include(
            "missing_persons_match_unidentified_dead_bodies.ajax.urls",
            namespace="ajax",
        ),
    ),
    path("drf/api-auth/", include("rest_framework.urls")),
    path(
        "drf/",
        include(
            "missing_persons_match_unidentified_dead_bodies.drf.urls",
            namespace="drf",
        ),
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
