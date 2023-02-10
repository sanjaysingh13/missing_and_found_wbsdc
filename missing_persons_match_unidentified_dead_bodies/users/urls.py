from django.urls import path

from missing_persons_match_unidentified_dead_bodies.users.views import (
    user_detail_view,
    user_redirect_view,
    user_update_view,
)

from . import views

app_name = "users"
urlpatterns = [
    path("district_admins/", views.district_admins, name="district_admins"),
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("<str:username>/", view=user_detail_view, name="detail"),
    path("<str:username>/edit/", views.edit_user, name="edit_user"),
    path(
        "<str:username>/change_password/", views.change_password, name="change_password"
    ),
]
