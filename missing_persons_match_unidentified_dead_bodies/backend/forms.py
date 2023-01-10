from datetime import datetime

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Column, Div, Field, Layout, Row, Submit
from django import forms
from django.core.validators import RegexValidator

from missing_persons_match_unidentified_dead_bodies.users.models import (
    District,
    PoliceStation,
)

GENDER = [("M", "Male"), ("F", "Female"), ("U", "Unknown")]
MISSING_OR_FOUND = [("M", "Missing"), ("F", "Found")]
# POLICE_STATIONS = [
#         (ps.id, ps.ps_with_distt)
#         for ps in PoliceStation.objects.all().order_by("ps_with_distt")
#     ]
DISTRICTS = [
    (distt.id, distt.name) for distt in District.objects.all().order_by("name")
]
DISTRICTS.insert(0, ("Null", "Select a District"))
YEARS = [
    (str(n).rjust(2, "0"), str(n).rjust(2, "0"))
    for n in range(0, datetime.now().year - 1999)
]
YEARS.insert(0, ("", "Select a year"))
FULL_TEXT_SEARCH_TYPE = []
FULL_TEXT_SEARCH_TYPE.append(
    (
        0,
        """Strict - fastest
    (when you are sure of the exact spelling of word e.g.
     "tattoo of Shiva")""",
    )
)
FULL_TEXT_SEARCH_TYPE.append(
    (
        1,
        """Partial word - slow
    (when you are searching for words within words e.g.
    gold will also return results for golden, marigold etc. )""",
    )
)
FULL_TEXT_SEARCH_TYPE.append(
    (
        2,
        """Fuzzy - slowest
    (Will return all approximate matches e.g.
    "sari"  will also be returned for "Saree")""",
    )
)

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
    latitude = forms.FloatField(required=False)
    longitude = forms.FloatField(required=False)

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
                    Row(HTML("<div id='map' class='map'></div>")),
                    css_class="col-md-6 mb-0",
                ),
                css_class="row",
            )
        )

        self.helper.form_method = "post"
        self.helper.form_tag = False
        self.helper.add_input(Submit("submit", "Submit"))


#######################


class ReportSearchForm(forms.Form):
    police_station_with_distt = forms.CharField(
        required=False, label="Police Station", max_length=100
    )
    ref_no = forms.CharField(
        label="Reference Number", widget=forms.TextInput(), required=False
    )
    ref_date = forms.DateField(required=False)
    ref_year = forms.ChoiceField(choices=YEARS, required=False)
    advanced_search_report = forms.BooleanField(label="Advanced Search", required=False)
    districts = forms.ChoiceField(choices=DISTRICTS, required=False)
    keywords = forms.CharField(
        label="Keywords",
        widget=forms.TextInput(attrs={"placeholder": "Muthoot"}),
        required=False,
        max_length=100,
        validators=[
            RegexValidator("^((?!AND).)*$", message="Cannot contain 'AND' "),
            RegexValidator("^((?!NOT).)*$", message="Cannot contain 'NOT' "),
        ],
    )
    full_text_search_type = forms.IntegerField(
        label="Keyword Search Type",
        widget=forms.RadioSelect(choices=FULL_TEXT_SEARCH_TYPE),
    )
    missing_or_found = forms.CharField(
        label="Missing or Found",
        widget=forms.RadioSelect(choices=[("All", "All")] + MISSING_OR_FOUND),
    )
    gender = forms.CharField(
        label="Gender", widget=forms.RadioSelect(choices=[("All", "All")] + GENDER[:-1])
    )
    min_date = forms.DateField()
    max_date = forms.DateField()
    ps_list = forms.CharField(required=False, widget=forms.HiddenInput())
    latitude = forms.CharField(required=False, max_length=20)
    longitude = forms.CharField(required=False, max_length=20)
    distance = forms.IntegerField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column(
                    "police_station_with_distt", css_class="form-group col-md-5 mb-0"
                ),
                Column("ref_no", css_class="form-group col-md-3 mb-0"),
                Column("ref_date", css_class="form-group col-md-3 mb-0"),
                Column("ref_year", css_class="form-group col-md-1 mb-0"),
                css_class="basic-search-fields",
            ),
            Field(
                "advanced_search_report",
                wrapper_class="custom-switch custom-control",
                show_all_fields="show_all_fields",
            ),
            HTML(
                """
                <div class="ui-widget advanced-search-fields">
                <h4> Select Police Stations.  </h4>
                <select class="form-select" aria-label="Default select example", id="police_station_id">
                <option value=""></option>
                </select>
                <div class="panel panel-default">
                <div class="panel-heading">
                <h3 class="panel-title">Selected PSs appear here</h3>
                </div>
                <div class="panel-body">
                <p id ="psquery"></p>
                </div>
                </div>
                </div>"""
            ),
            Div(
                Row(
                    Column("districts", css_class="form-group col-md-3 mb-0"),
                    Column("keywords", css_class="form-group col-md-4 mb-0"),
                    Column(
                        "full_text_search_type", css_class="form-group col-md-5 mb-0"
                    ),
                    Field("ps_list", type="hidden"),
                ),
                Row(
                    Column("gender", css_class="form-group col-md-3 mb-0"),
                    Column("missing_or_found", css_class="form-group col-md-3 mb-0"),
                    Column("min_date", css_class="form-group col-md-3 mb-0"),
                    Column("max_date", css_class="form-group col-md-3 mb-0"),
                ),
                Row(
                    HTML(
                        """<p class = col-md-3>
                        You can specify a lat/long and distance in Km
                        to search for reports within a circle</p>"""
                    ),
                    Column("latitude", css_class="form-group col-md-3 mb-0"),
                    Column("longitude", css_class="form-group col-md-3 mb-0"),
                    Column("distance", css_class="form-group col-md-3 mb-0"),
                ),
                Row(HTML("<div id='map' class='map'></div>")),
                css_class="advanced-search-fields ",
            ),
        )
        self.helper.form_id = "id-exampleForm"
        self.helper.form_class = "blueForms"
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Submit"))

    def clean(self):
        cleaned_data = super().clean()
        messages = []
        if not cleaned_data.get("advanced_search_report"):
            no_ps = cleaned_data.get("police_station_with_distt", "") == ""
            no_ref_no = cleaned_data.get("ref_no", "") == ""
            no_ref_date = cleaned_data.get("ref_date", "")
            no_ref_year = cleaned_data.get("ref_year", "") == ""
            if no_ps or no_ref_no or (no_ref_date and no_ref_year):
                msg = "PS, case number, case date or case year required "
                messages.append(msg)
            if cleaned_data.get("ref_no", "") != "" and (
                not cleaned_data.get("ref_no", "").isdigit()
            ):
                msg_ = "Case number has to be just a number (without year)"
                messages.append(msg_)
        else:
            pass
        if messages != []:
            raise forms.ValidationError(messages)

        return cleaned_data
