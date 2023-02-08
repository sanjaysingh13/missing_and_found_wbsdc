from django.urls import include, path
from rest_framework import routers

from missing_persons_match_unidentified_dead_bodies.backend import views

router = routers.DefaultRouter()

router.register(r"reports", views.ReportViewSet)
# router.register(r'search_reports', views.ReportSearchViewSet)

app_name = "backend"

urlpatterns = [
    path("", include(router.urls)),
    path("public/", views.public, name="public"),
    path("upload_photo/", views.upload_photo, name="upload_photo"),
    path(
        "upload_public_report/", views.upload_public_report, name="upload_public_report"
    ),
    path("view_report/<int:object_id>/", views.view_report, name="view_report"),
    path(
        "view_public_report/<str:object_id>/",
        views.view_public_report,
        name="view_public_report",
    ),
    path("edit_report/<int:pk>/", views.edit_report, name="edit_report"),
    path("report_search/", views.report_search, name="report_search"),
    path(
        "advanced_report_search/<int:pk>",
        views.report_search_results,
        name="advanced_report_search",
    ),
    path("bounded_box_search/", views.bounded_box_search, name="bounded_box_search"),
    path("matches/", views.matches, name="matches"),
    path("report/<pk>/delete/", views.ReportDeleteView.as_view(), name="report_delete"),
    path("district/", views.district, name="district"),
]
