from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, RedirectView, UpdateView

from .forms import EditUserForm

User = get_user_model()


class UserDetailView(LoginRequiredMixin, DetailView):

    model = User
    slug_field = "username"
    slug_url_kwarg = "username"


user_detail_view = UserDetailView.as_view()


@login_required
def edit_user(request, username):
    user = User.objects.get(username=username)
    if request.method == "POST":
        form = EditUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect("users:detail", username=username)
    else:
        form = EditUserForm(instance=user)
    return render(request, "users/edit_user.html", {"form": form})


@login_required
def change_password(request, username):
    user = User.objects.get(username=username)
    if request.method == "POST":
        password_form = PasswordChangeForm(user, request.POST)
        if password_form.is_valid():
            password_form.save()
            update_session_auth_hash(request, password_form.user)
            return redirect("users:detail", username=username)
    else:
        password_form = PasswordChangeForm(request.user)
    return render(
        request, "users/password_change.html", {"password_form": password_form}
    )


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):

    model = User
    fields = ["name"]
    success_message = _("Information successfully updated")

    def get_success_url(self):
        assert (
            self.request.user.is_authenticated
        )  # for mypy to know that the user is authenticated
        return self.request.user.get_absolute_url()

    def get_object(self):
        return self.request.user


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):

    permanent = False

    def get_redirect_url(self):
        return reverse("users:detail", kwargs={"username": self.request.user.username})


user_redirect_view = UserRedirectView.as_view()


def district_admins(request):
    template_name = "users/district_admins.html"
    district_admins = [
        (user.name, user.email, user.telephone, user.district.name)
        for user in User.objects.filter(category="DISTRICT_ADMIN")
        .exclude(is_sp_or_cp=True)
        .exclude(is_staff=False)
        .order_by("district__name")
    ]
    return render(
        request,
        template_name,
        {
            "district_admins": district_admins,
        },
    )
