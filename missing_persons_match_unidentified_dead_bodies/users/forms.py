from allauth.account.forms import LoginForm, SignupForm
from captcha.fields import ReCaptchaField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Layout, Row, Submit
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


class EditUserForm(forms.ModelForm):
    telephone = forms.CharField(required=True, max_length=10)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "name",
            "telephone",
            "rank",
            "police_station",
            "district",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column("username", css_class="form-group col-md-3 mb-0"),
                Column("email", css_class="form-group col-md-3 mb-0"),
                Column("name", css_class="form-group col-md-3 mb-0"),
                Column("rank", css_class="form-group col-md-3 mb-0"),
                css_class="form-row",
            ),
            Row(
                Column("telephone", css_class="form-group col-md-4 mb-0"),
                Column("police_station", css_class="form-group col-md-4 mb-0"),
                Column("district", css_class="form-group col-md-4 mb-0"),
                css_class="form-row",
            ),
            Submit("submit", "Save Changes"),
        )


class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(label="Old password", widget=forms.PasswordInput)
    new_password1 = forms.CharField(label="New password", widget=forms.PasswordInput)
    new_password2 = forms.CharField(
        label="Confirm new password", widget=forms.PasswordInput
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_new_password2(self):
        password1 = self.cleaned_data.get("new_password1")
        password2 = self.cleaned_data.get("new_password2")
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        password = self.cleaned_data["new_password1"]
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user


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
        user = super(CustomSignupForm, self).save(request)
        if user:
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
