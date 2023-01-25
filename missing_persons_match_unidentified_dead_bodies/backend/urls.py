from django.urls import path

from missing_persons_match_unidentified_dead_bodies.backend import views

app_name = "backend"

urlpatterns = [
    path("upload_photo/", views.upload_photo, name="upload_photo"),
    path("view_report/<int:object_id>/", views.view_report, name="view_report"),
    path("report_search/", views.report_search, name="report_search"),
    path(
        "river_search/<str:latitude>/<str:longitude>/",
        views.river_search,
        name="river_search",
    ),
    path(
        "get_river_search_location/",
        views.get_river_search_location,
        name="get_river_search_location",
    ),
    path("matches/", views.matches, name="matches"),
    path("report/<pk>/delete/", views.ReportDeleteView.as_view(), name="report_delete"),
]
