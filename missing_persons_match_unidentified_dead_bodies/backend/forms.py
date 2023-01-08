# from crispy_forms.bootstrap import FieldWithButtons, StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Div, Layout, Row, Submit
from django import forms
from django.core.validators import RegexValidator

from missing_persons_match_unidentified_dead_bodies.users.models import PoliceStation

GENDER = [("M", "MALE"), ("F", "FEMALE"), ("U", "UNKNOWN")]
MISSING_OR_FOUND = [("M", "MISSING"), ("F", "FOUND")]
try:
    ps_list = [
        (ps["id"], ps["ps_with_distt"])
        for ps in PoliceStation.objects.all().order_by("ps_with_distt").values()
    ]
except Exception as e:
    print(str(e))
    ps_list = [("foo", "foo")]
##########################


class ReportForm(forms.Form):
    photo = forms.FileField(
        label="Photos ", required=False, widget=forms.ClearableFileInput()
    )
    police_station_with_distt = forms.CharField(
        label="Police Station",
        max_length=100,
        validators=[
            RegexValidator(
                r".*:.*",
                message='Your internet is slow. Police Station name must be of form "PS Name : District name"',
                code="invalid_ps",
            ),
        ],
    )
    # police_station_with_distt = forms.ChoiceField(choices=ps_list, required=False)
    entry_date = forms.DateField(required=False)
    name = forms.CharField(required=False, label="Name", max_length=100)
    gender = forms.CharField(label="Gender", widget=forms.RadioSelect(choices=GENDER))
    missing_or_found = forms.CharField(
        label="Missing or Found", widget=forms.RadioSelect(choices=MISSING_OR_FOUND)
    )
    height = forms.IntegerField()
    description = forms.CharField(max_length=500, widget=forms.Textarea())
    latitude = forms.CharField(required=False, max_length=20)
    longitude = forms.CharField(required=False, max_length=20)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Column(
                    Row("photo", css_class="form-group"),
                    Row("missing_or_found", css_class="form-group"),
                    Row("name", css_class="form-group "),
                    Row("description", css_class="form-group"),
                    css_class="col-md-6 mb-0",
                ),
                Column(
                    Row("height", css_class="form-group"),
                    Row("gender", css_class="form-group"),
                    Row("entry_date", css_class="form-group "),
                    Row("latitude", css_class="form-group "),
                    Row("longitude", css_class="form-group "),
                    Row("police_station_with_distt", css_class="form-group"),
                    css_class="col-md-6 mb-0",
                ),
                css_class="row",
            )
        )

        self.helper.form_method = "post"
        self.helper.form_tag = False
        self.helper.add_input(Submit("submit", "Submit"))
