from django.urls import path

from missing_persons_match_unidentified_dead_bodies.backend import views

app_name = "backend"

urlpatterns = [
    path("upload_photo/", views.upload_photo, name="upload_photo"),
    path("view_report/<int:object_id>/", views.view_report, name="view_report"),
]
