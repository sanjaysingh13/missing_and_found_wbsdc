from allauth.account.forms import LoginForm, SignupForm
from captcha.fields import ReCaptchaField
from django import forms
from django.contrib.auth import forms as admin_forms
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from missing_persons_match_unidentified_dead_bodies.users.models import (
    District,
    PoliceStation,
)

try:
    POLICE_STATIONS = [
        (ps.id, ps.ps_with_distt)
        for ps in PoliceStation.objects.all().order_by("ps_with_distt")
    ]
    POLICE_STATIONS = [(None, "---")] + POLICE_STATIONS
    DISTRICTS = [
        (distt.id, distt.name) for distt in District.objects.all().order_by("name")
    ]
    DISTRICTS = [(None, "---")] + DISTRICTS
except Exception as e:
    print(str(e))
    POLICE_STATIONS = [("foo", "foo")]
    DISTRICTS = [("bar", "bar")]

User = get_user_model()


class UserChangeForm(admin_forms.UserChangeForm):
    class Meta(admin_forms.UserChangeForm.Meta):
        model = User


class UserCreationForm(admin_forms.UserCreationForm):
    class Meta(admin_forms.UserCreationForm.Meta):
        model = User

        error_messages = {
            "username": {"unique": _("This username has already been taken.")}
        }


class CustomSignupForm(SignupForm):
    captcha = ReCaptchaField()
    name = forms.CharField(max_length=100)
    rank = forms.CharField(max_length=50, label="Rank")
    telephone = forms.CharField(
        max_length=10,
        label="Telephone",
        validators=[
            RegexValidator(
                r"\d{10}",
                message="Telephone number must be 10-digit",
                code="invalid_telephone",
            ),
        ],
    )
    police_station = forms.ChoiceField(
        required=False, choices=POLICE_STATIONS, label="Police Station"
    )
    district = forms.ChoiceField(required=False, choices=DISTRICTS, label="District")

    def save(self, request):
        user = super().save(request)
        print(self.cleaned_data)
        user.name = self.cleaned_data["name"]
        user.rank = self.cleaned_data["rank"]
        user.telephone = self.cleaned_data["telephone"]
        if self.cleaned_data["district"]:
            user.district_id = self.cleaned_data["district"]
        if self.cleaned_data["police_station"]:
            user.police_station_id = self.cleaned_data["police_station"]
            user.district_id = PoliceStation.objects.get(
                id=self.cleaned_data["police_station"]
            ).district_id
        user.save()
        return user


class CustomLoginForm(LoginForm):
    captcha = ReCaptchaField()
