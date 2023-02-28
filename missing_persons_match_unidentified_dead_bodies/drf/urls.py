from django.urls import include, path
from rest_framework import routers

from missing_persons_match_unidentified_dead_bodies.drf import views

app_name = "drf"
# Serializers define the API representation.


# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r"reports", views.ReportViewSet)
router.register(r"users", views.UserViewSet)


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path("", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path(
        "search_reports",
        views.search_reports,
        name="search_reports",
    ),
]
