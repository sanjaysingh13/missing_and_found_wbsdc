from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from rest_framework import routers

from missing_persons_match_unidentified_dead_bodies.backend import views

from .sitemap import StaticViewSitemap

router = routers.DefaultRouter()

router.register(r"reports", views.ReportViewSet)
# router.register(r'search_reports', views.ReportSearchViewSet)

app_name = "backend"
sitemaps = {
    "static": StaticViewSitemap,
}

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
        "public_report_search/", views.public_report_search, name="public_report_search"
    ),
    path(
        "advanced_report_search/<int:pk>",
        views.report_search_results,
        name="advanced_report_search",
    ),
    path("bounded_box_search/", views.bounded_box_search, name="bounded_box_search"),
    path("matches/<str:category>/", views.matches, name="matches"),
    path("report/<pk>/delete/", views.ReportDeleteView.as_view(), name="report_delete"),
    path("district/", views.district, name="district"),
    path(
        "districts_at_glance_reports/",
        views.districts_at_glance_reports,
        name="districts_at_glance_reports",
    ),
    path(
        "users_at_glance/",
        views.users_at_glance,
        name="users_at_glance",
    ),
    path(
        "districts_at_glance_public_reports/",
        views.districts_at_glance_public_reports,
        name="districts_at_glance_public_reports",
    ),
    path(
        "public_reports_by_district/<str:name>/",
        views.public_reports_by_district,
        name="public_reports_by_district",
    ),
    path(
        "reports_by_district/<str:name>/",
        views.reports_by_district,
        name="reports_by_district",
    ),
    path(
        "handle_sendgrid_post/", views.handle_sendgrid_post, name="handle_sendgrid_post"
    ),
    path(
        "seven_days_missing/",
        views.seven_days_missing,
        name="seven_days_missing",
    ),
    path(
        "seven_days_public_missing/",
        views.seven_days_public_missing,
        name="seven_days_public_missing",
    ),
    path(
        "seven_days_found/",
        views.seven_days_found,
        name="seven_days_found",
    ),
    path(
        "comment_form/",
        views.comment_form,
        name="comment_form",
    ),
    path(
        "comments/",
        views.comments,
        name="comments",
    ),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
]
