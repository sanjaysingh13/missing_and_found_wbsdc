from django.urls import path

from missing_persons_match_unidentified_dead_bodies.ajax import views

app_name = "ajax"

urlpatterns = [
    # Backend
    path("public_missing/", views.public_missing, name="get_ajax_public_missing"),
]
