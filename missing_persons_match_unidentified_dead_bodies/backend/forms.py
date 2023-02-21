from datetime import datetime

from captcha.fields import ReCaptchaField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Button, Column, Div, Field, Layout, Row, Submit
from django import forms
from django.core.validators import RegexValidator
from mapbox_location_field.spatial.forms import SpatialLocationField

from missing_persons_match_unidentified_dead_bodies.users.models import (
    District,
    PoliceStation,
)

GENDER = [("Male", "Male"), ("Female", "Female"), ("U", "Unknown")]
MISSING_OR_FOUND = [
    ("M", "Missing"),
    ("F", "Unidentified Dead Body"),
    ("U", "Unidentified Recovered Person"),
]
GDE_OR_FIR = [
    ("GDE", "GDE"),
    ("FIR", "FIR"),
]
# POLICE_STATIONS = [
#         (ps.id, ps.ps_with_distt)
#         for ps in PoliceStation.objects.all().order_by("ps_with_distt")
#     ]
try:
    DISTRICTS = [
        (distt.id, distt.name) for distt in District.objects.all().order_by("name")
    ]
except Exception as e:
    print(str(e))
    DISTRICTS = [("bar", "bar")]
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
        """Fuzzy -
    (Will return all approximate matches e.g.
    "sari"  will also be returned for "Saree")""",
    )
)
default_map_attrs = {
    "style": "mapbox://styles/mapbox/outdoors-v11",
    "zoom": 13,
    "center": [88.3639, 22.5726],
    "cursor_style": "pointer",
    "marker_color": "red",
    "rotate": False,
    "geocoder": True,
    "fullscreen_button": True,
    "navigation_buttons": True,
    "track_location_button": True,
    "readonly": True,
    "placeholder": "Pick a location on map below",
    "language": "auto",
    "message_404": "undefined address",
}
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
    photo = forms.ImageField(label="Photos ", widget=forms.ClearableFileInput())
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
    reference = forms.IntegerField()
    gde_or_fir = forms.CharField(
        label="GDE or FIR",
        widget=forms.RadioSelect(choices=GDE_OR_FIR),
    )
    entry_date = forms.DateField(label="Ref Date")
    name = forms.CharField(required=False, label="Name", max_length=100)
    gender = forms.CharField(label="Gender", widget=forms.RadioSelect(choices=GENDER))
    missing_or_found = forms.CharField(
        label="Missing or Unidentified Dead Body",
        widget=forms.RadioSelect(choices=MISSING_OR_FOUND),
    )
    height = forms.IntegerField()
    age = forms.IntegerField()
    guardian_name_and_address = forms.CharField(max_length=300, required=False)
    description = forms.CharField(max_length=500, widget=forms.Textarea())
    latitude = forms.FloatField(required=False)
    longitude = forms.FloatField(required=False)
    location = SpatialLocationField(map_attrs=default_map_attrs, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Column(
                    Row(
                        Column(
                            "photo",
                            css_class="form-group card text-dark bg-light col-md-6 mb-0",
                        ),
                        HTML(
                            """<p class='col-md-6 mb-0 card text-white bg-primary'>
                            Use a clear, vertical frontal face picture if possible.
                            In case of mutilation by accident, take a clear picture
                            after stitching of injuries.
                            </p>"""
                        ),
                    ),
                    Row(HTML("</br>")),
                    Row(
                        Column(
                            "missing_or_found",
                            css_class="form-group col-md-6 mb-0 card text-dark bg-light",
                        ),
                        Column(
                            "gender",
                            css_class="form-group col-md-6 mb-0 card text-dark bg-light",
                        ),
                    ),
                    Row("name", css_class="form-group "),
                    Row("guardian_name_and_address", css_class="form-group "),
                    Row("police_station_with_distt", css_class="form-group"),
                    Row("reference", css_class="form-group "),
                    Row("gde_or_fir", css_class="form-group "),
                    css_class="col-md-6 mb-0",
                ),
                Column(
                    Row(
                        Column(
                            "height",
                            css_class="form-group card text-dark bg-light col-md-6 mb-0",
                        ),
                        HTML(
                            """<p class='col-md-6 mb-0 card text-white bg-primary'>
                            It is very important to record height.
                            For dead bodies, measure it in prone position.
                            For missing perons, make a best guess by recording
                            statements of 3/4 close acquaintances.</p>"""
                        ),
                    ),
                    Row("age", css_class="form-group"),
                    Row("description", css_class="form-group"),
                    Row("entry_date", css_class="form-group "),
                    Row(HTML("<div id='map' class='map'></div>")),
                    css_class="col-md-6 mb-0",
                ),
                css_class="row",
            ),
            HTML("<hr>"),
            Div(
                Row(
                    HTML(
                        """<p class='col-md-12 mb-0 card-title'>
                        You can enter location by either selecting a point on the map, or supplying lat/long manually.
                        For dead bodies, it will be the location where found.
                        For missing persons,
                        the EO must visit or otherwise ascertain the last known location
                        and record it's coordinates.</p>"""
                    )
                ),
                Row(HTML("</br>")),
                Row(
                    Column("location", css_class="form-group col-md-8 mb-0"),
                    Column("latitude", css_class="form-group col-md-2 mb-0"),
                    Column("longitude", css_class="form-group col-md-2 mb-0"),
                ),
                css_class="row card text-dark bg-light",
            ),
        )

        self.helper.form_method = "post"
        self.helper.form_tag = False
        self.helper.add_input(Submit("submit", "Submit"))

    def clean(self):
        cleaned_data = super().clean()
        messages = []
        latitude = cleaned_data.get("latitude")
        longitude = cleaned_data.get("longitude", "")
        missing_or_found = cleaned_data.get("missing_or_found", "")
        name = cleaned_data.get("name", "")
        if missing_or_found == "F" and name:
            msg_ = "An unidentified dead body cannot have a name"
            messages.append(msg_)

        if latitude:
            if not longitude:
                msg_ = "Please fill both lat and long"
                messages.append(msg_)
            else:
                if (not (21 <= latitude <= 28)) or (not (86.5 <= longitude <= 90)):
                    msg_ = "Please fill lat and long within the State of West Bengal."
                    messages.append(msg_)
        if longitude:
            if not latitude:
                msg_ = "Please fill both lat and long"
                messages.append(msg_)
            else:
                if (not (21 <= latitude <= 28)) or (not (86.5 <= longitude <= 90)):
                    msg_ = "Please fill lat and long within the State of West Bengal."
                    messages.append(msg_)
        photo = cleaned_data.get("photo")
        if photo:
            if photo.size > 5 * 1024 * 1024:
                msg_ = "Please pick image below 5 Mb"
                messages.append(msg_)
        else:
            msg_ = "Please pick an image"
            messages.append(msg_)
        if messages != []:
            messages = list(set(messages))
            raise forms.ValidationError(messages)

        return cleaned_data


class PublicReportForm(forms.Form):
    acknowledgement_checkbox = forms.BooleanField(label="Acknowledgement")
    captcha = ReCaptchaField()
    photo = forms.ImageField(label="Photos ", widget=forms.ClearableFileInput())
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
    entry_date = forms.DateField(label="Date of Missing")
    name = forms.CharField(
        required=False, label="Name of Missing Person", max_length=100
    )
    gender = forms.CharField(
        label="Gender",
        widget=forms.RadioSelect(choices=[("M", "Male"), ("F", "Female")]),
    )
    height = forms.IntegerField()
    age = forms.IntegerField()
    guardian_name_and_address = forms.CharField(max_length=300, required=False)
    telephone_of_missing = forms.CharField(
        required=False,
        label="Missing person's phone (10 digits)",
        max_length=10,
        validators=[
            RegexValidator(
                r"\d{10}",
                message="Telephone number must be 10-digit",
                code="invalid_telephone",
            ),
        ],
    )
    telephone_of_reporter = forms.CharField(
        label="Your telephone (10 digits)",
        max_length=10,
        validators=[
            RegexValidator(
                r"\d{10}",
                message="Telephone number must be 10-digit",
                code="invalid_telephone",
            ),
        ],
    )
    email_of_reporter = forms.EmailField(label="Your Email")
    description = forms.CharField(max_length=500, widget=forms.Textarea())
    location = SpatialLocationField(map_attrs=default_map_attrs)
    otp = forms.CharField(
        label="Check your Phone for OTP", max_length=6, required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Row(
                    HTML(
                        "<p class='col-md-12 mb-0 card text-white bg-danger'>"
                        + "1) I understand that this is not a legal document. "
                        + " I must visit the Police Station with the token "
                        + "given to me and validate my input"
                        + " given here physically.</br>"
                        + "2) The missing person is not a minor. "
                        + "  As per the orders of the Hon'ble Supreme Court of India,"
                        + " I must visit the Police Station physically "
                        + " to register a specific FIR "
                        + "if the missing person is a minor.</p>"
                    ),
                ),
                Row(
                    Column(
                        "acknowledgement_checkbox",
                        css_class="form-group  col-md-6 mb-0",
                    ),
                ),
            ),
            Div(
                Column(
                    Row(
                        Column(
                            "photo",
                            css_class="form-group card text-dark bg-light col-md-6 mb-0",
                        ),
                        HTML(
                            """<p class='col-md-6 mb-0 card text-white bg-primary'>
                            Use a clear, vertical frontal face picture.
                            </p>"""
                        ),
                    ),
                    Row(HTML("</br>")),
                    Column(
                        Row("telephone_of_missing"),
                        Row("telephone_of_reporter"),
                        Row("email_of_reporter"),
                        css_class="form-group col-md-12 mb-0 card text-dark bg-light",
                    ),
                    Column(
                        "gender",
                        css_class="form-group col-md-12 mb-0 card text-dark bg-light",
                    ),
                    Row("name", css_class="form-group "),
                    Row("guardian_name_and_address", css_class="form-group "),
                    Row("police_station_with_distt", css_class="form-group"),
                    css_class="col-md-6 mb-0",
                ),
                Column(
                    Row(
                        Column(
                            "height",
                            css_class="form-group card text-dark bg-light col-md-6 mb-0",
                        ),
                        HTML(
                            """<p class='col-md-6 mb-0 card text-white bg-primary'>
                            It is very important to record height.
                            Make a best guess by recording
                            statements of 3/4 close acquaintances.</p>"""
                        ),
                    ),
                    Row("age", css_class="form-group"),
                    Row("description", css_class="form-group"),
                    Row("entry_date", css_class="form-group "),
                    Row("captcha", css_class="form-group "),
                    Row(HTML("<div id='map' class='map'></div>")),
                    css_class="col-md-6 mb-0",
                ),
                css_class="row",
            ),
            HTML("<hr>"),
            Div(
                Row(
                    HTML(
                        "<p class='col-md-12 mb-0 card-title'>"
                        + "You can enter location where missing person was "
                        + "last seen by selecting a point on the map,</p>"
                    )
                ),
                Row(HTML("</br>")),
                Row(
                    Column("location", css_class="form-group col-md-8 mb-0"),
                ),
                css_class="row card text-dark bg-light",
            ),
            Row(Column("otp", required=False, css_class="form-group col-md-2 mb-0")),
        )

        self.helper.form_method = "post"
        self.helper.form_tag = False
        self.helper.form_id = "blueForms"
        self.helper.add_input(Submit("submit", "Submit"))

    def clean(self):
        cleaned_data = super().clean()
        messages = []
        age = cleaned_data.get("age", "")
        photo = cleaned_data.get("photo")
        if photo:
            if photo.size > 5 * 1024 * 1024:
                msg_ = "Please pick image below 5 Mb"
                messages.append(msg_)
        else:
            msg_ = "Please pick an image"
            messages.append(msg_)
        if age < 18:
            msg_ = "The missing person is a minor. Please visit the Police Station and register a specific FIR"
            messages.append(msg_)

        if messages != []:
            messages = list(set(messages))
            raise forms.ValidationError(messages)

        return cleaned_data


class ReportFormEdit(forms.Form):
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
    reference = forms.IntegerField()
    entry_date = forms.DateField(label="Ref Date")
    name = forms.CharField(required=False, label="Name", max_length=100)
    gender = forms.CharField(label="Gender", widget=forms.RadioSelect(choices=GENDER))
    missing_or_found = forms.CharField(
        label="Missing or Found", widget=forms.RadioSelect(choices=MISSING_OR_FOUND)
    )
    height = forms.IntegerField()
    age = forms.IntegerField()
    guardian_name_and_address = forms.CharField(
        max_length=300, required=False, widget=forms.Textarea()
    )
    description = forms.CharField(max_length=500, widget=forms.Textarea())
    latitude = forms.FloatField(required=False)
    longitude = forms.FloatField(required=False)
    location = SpatialLocationField(map_attrs=default_map_attrs, required=False)
    reconciled = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Column(
                    Row(HTML("</br>")),
                    Row(
                        Column(
                            "missing_or_found",
                            css_class="form-group col-md-4 mb-0 card text-dark bg-light",
                        ),
                        Column(
                            "reconciled",
                            css_class="form-group col-md-4 mb-0 card text-dark bg-light",
                        ),
                        Column(
                            "gender",
                            css_class="form-group col-md-4 mb-0 card text-dark bg-light",
                        ),
                    ),
                    Row("name", css_class="form-group "),
                    Row("guardian_name_and_address", css_class="form-group "),
                    Row("police_station_with_distt", css_class="form-group"),
                    css_class="col-md-6 mb-0",
                ),
                Column(
                    Row(
                        Column(
                            "height",
                            css_class="form-group card text-dark bg-light col-md-6 mb-0",
                        ),
                        HTML(
                            """<p class='col-md-6 mb-0 card text-white bg-primary'>
                            It is very important to record height.
                            For dead bodies, measure it in prone position.
                            For missing perons, make a best guess by recording
                            statements of 3/4 close acquaintances.</p>"""
                        ),
                    ),
                    Row("age", css_class="form-group"),
                    Row("description", css_class="form-group"),
                    Row("reference", css_class="form-group "),
                    Row("entry_date", css_class="form-group "),
                    Row(HTML("<div id='map' class='map'></div>")),
                    css_class="col-md-6 mb-0",
                ),
                css_class="row",
            ),
            HTML("<hr>"),
            Div(
                Row(
                    HTML(
                        """<p class='col-md-12 mb-0 card-title'>
                        You can enter location by either selecting a point on the map, or supplying lat/long manually.
                        For dead bodies, it will be the location where found.
                        For missing persons,
                        the EO must visit or otherwise ascertain the last known location
                        and record it's coordinates.</p>"""
                    )
                ),
                Row(HTML("</br>")),
                Row(
                    Column("location", css_class="form-group col-md-8 mb-0"),
                    Column("latitude", css_class="form-group col-md-2 mb-0"),
                    Column("longitude", css_class="form-group col-md-2 mb-0"),
                ),
                css_class="row card text-dark bg-light",
            ),
        )

        self.helper.form_method = "post"
        self.helper.form_tag = False
        self.helper.add_input(Submit("submit", "Submit"))

    def clean(self):
        cleaned_data = super().clean()
        messages = []
        latitude = cleaned_data.get("latitude")
        longitude = cleaned_data.get("longitude", "")
        if latitude:
            if not longitude:
                msg_ = "Please fill both lat and long"
                messages.append(msg_)
            else:
                if (not (21 <= latitude <= 28)) or (not (86.5 <= longitude <= 90)):
                    msg_ = "Please fill lat and long within the State of West Bengal."
                    messages.append(msg_)
        if longitude:
            if not latitude:
                msg_ = "Please fill both lat and long"
                messages.append(msg_)
            else:
                if (not (21 <= latitude <= 28)) or (not (86.5 <= longitude <= 90)):
                    msg_ = "Please fill lat and long within the State of West Bengal."
                    messages.append(msg_)
        if messages != []:
            messages = list(set(messages))
            raise forms.ValidationError(messages)

        return cleaned_data


#######################


class ReportSearchForm(forms.Form):
    police_station_with_distt = forms.CharField(
        required=False, label="Police Station", max_length=100
    )
    ref_no = forms.CharField(
        label="Reference Number", widget=forms.TextInput(), required=False
    )
    gde_or_fir = forms.CharField(
        label="GDE or FIR",
        widget=forms.RadioSelect(choices=GDE_OR_FIR),
    )
    ref_date = forms.DateField(required=False)
    ref_year = forms.ChoiceField(choices=YEARS, required=False)
    advanced_search_report = forms.BooleanField(label="Advanced Search", required=False)
    districts = forms.ChoiceField(choices=DISTRICTS, required=False)
    keywords = forms.CharField(
        label="Keywords",
        widget=forms.TextInput(attrs={"placeholder": "mole on left hand"}),
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
        required=False,
        widget=forms.RadioSelect(choices=[("All", "All")] + MISSING_OR_FOUND),
    )
    gender = forms.CharField(
        label="Gender",
        required=False,
        widget=forms.RadioSelect(choices=[("All", "All")] + GENDER[:-1]),
    )
    min_date = forms.DateField(required=False)
    max_date = forms.DateField(required=False)
    ps_list = forms.CharField(required=False, widget=forms.HiddenInput())
    latitude = forms.CharField(required=False, max_length=20)
    longitude = forms.CharField(required=False, max_length=20)
    location = SpatialLocationField(map_attrs=default_map_attrs, required=False)
    distance = forms.IntegerField(required=False)
    map_or_list = forms.CharField(
        label="Map or List",
        required=False,
        widget=forms.RadioSelect(choices=[("M", "Map"), ("L", "List")]),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column(
                    "police_station_with_distt", css_class="form-group col-md-4 mb-0"
                ),
                Column("ref_no", css_class="form-group col-md-2 mb-0"),
                Column("gde_or_fir", css_class="form-group col-md-2 mb-0"),
                Column("ref_date", css_class="form-group col-md-2 mb-0"),
                Column("ref_year", css_class="form-group col-md-2 mb-0"),
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
                HTML(
                    """<p class = col-md-12>
                        You can specify a lat/long and distance in Km
                        to search for reports within a circle</p>"""
                ),
                Row(
                    Column(
                        Row("location", css_class="form-group "),
                        css_class="col-md-10 mb-0",
                    ),
                    Column(
                        Row("latitude", css_class="form-group "),
                        Row("longitude", css_class="form-group "),
                        Row("distance", css_class="form-group "),
                        Row("map_or_list", css_class="form-group "),
                        css_class="col-md-2 mb-0",
                    ),
                ),
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
            ps = cleaned_data.get("police_station_with_distt", "")
            no_ps = ps == ""
            ref_no = cleaned_data.get("ref_no", "")
            no_ref_no = ref_no == ""
            ref_date = cleaned_data.get("ref_date", "")
            ref_year = cleaned_data.get("ref_year", "")
            no_ref_year = ref_year == ""
            if no_ps or no_ref_no or ((not ref_date) and no_ref_year):
                msg = f"PS, case number, case date or case year required {ps}, {ref_no}, {ref_date} "
                messages.append(msg)
            if cleaned_data.get("ref_no", "") != "" and (
                not cleaned_data.get("ref_no", "").isdigit()
            ):
                msg_ = "Case number has to be just a number (without year)"
                messages.append(msg_)
        else:
            latitude = cleaned_data.get("latitude")
            longitude = cleaned_data.get("longitude", "")
            distance = cleaned_data.get("distance", "")
            location = cleaned_data.get("location", "")
            if latitude:
                latitude = float(latitude)
                if not longitude:
                    msg_ = "Please fill both lat and long"
                    messages.append(msg_)
                else:
                    longitude = float(longitude)
                    if (not (21 <= latitude <= 28)) or (not (86.5 <= longitude <= 90)):
                        msg_ = (
                            "Please fill lat and long within the State of West Bengal."
                        )
                        messages.append(msg_)
            if longitude:
                longitude = float(longitude)
                if not latitude:
                    msg_ = "Please fill both lat and long"
                    messages.append(msg_)
                else:
                    latitude = float(latitude)
                    if (not (21 <= latitude <= 28)) or (not (86.5 <= longitude <= 90)):
                        msg_ = (
                            "Please fill lat and long within the State of West Bengal."
                        )
                        messages.append(msg_)
            if latitude or location:
                if not distance:
                    msg_ = "Please enter a distance to search."
                    messages.append(msg_)

            if messages != []:
                messages = list(set(messages))
                raise forms.ValidationError(messages)

            return cleaned_data
        if messages != []:
            raise forms.ValidationError(messages)

        return cleaned_data


class BoundedBoxSearchForm(forms.Form):
    location = SpatialLocationField(map_attrs=default_map_attrs, required=False)
    gender = forms.CharField(
        label="Gender",
        required=False,
        widget=forms.RadioSelect(choices=GENDER[:-1]),
    )
    min_date = forms.DateField(required=False)
    max_date = forms.DateField(required=False)
    lines = forms.CharField(
        label="Type of Line",
        required=False,
        widget=forms.RadioSelect(
            choices=[
                ("waterlines", "River"),
                ("raillines", "Rail"),
                ("roadlines", "Road"),
            ]
        ),
    )
    north_west_location = forms.CharField(label="NW Corner")
    south_east_location = forms.CharField(label="SE Corner")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Row(
                    Column("gender", css_class="form-group col-md-3 mb-0"),
                    Column("min_date", css_class="form-group col-md-3 mb-0"),
                    Column("max_date", css_class="form-group col-md-3 mb-0"),
                    Column("lines", css_class="form-group col-md-3 mb-0"),
                ),
                Row(
                    HTML(
                        "<p> Select a box on the map by fixing"
                        + "North-West and South-West corner points"
                        + " of box from the given map.</p>"
                    ),
                    Column("north_west_location", css_class="form-group col-md-3 mb-0"),
                    Button("confirm_nw", "Confirm NW", css_class=" col-md-2 mb-0"),
                    Column(
                        "south_east_location",
                        label="SE Corner",
                        css_class="form-group col-md-3 mb-0",
                    ),
                    Button("confirm_se", "Confirm SE", css_class=" col-md-2 mb-0"),
                    Button("clear", "Clear", css_class=" col-md-2 mb-0"),
                ),
                Row(
                    Column("location", css_class="form-group"),
                ),
            ),
        )
        self.helper.form_id = "id-exampleForm"
        self.helper.form_class = "blueForms"
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Submit"))

    def clean(self):
        cleaned_data = super().clean()
        messages = []
        north_west_location = cleaned_data.get("north_west_location", "")
        south_east_location = cleaned_data.get("south_east_location", "")
        print("<<<")
        print(not (("," in north_west_location) and ("," in south_east_location)))
        if not (("," in north_west_location) and ("," in south_east_location)):
            print("wrong coordinates")
            msg_ = "Please select NW and SE corners correctly"
            messages.append(msg_)
        else:
            north_west_location = north_west_location.split(",")

            south_east_location = south_east_location.split(",")

            xmin = float(north_west_location[1])
            ymax = float(north_west_location[0])

            xmax = float(south_east_location[1])
            ymin = float(south_east_location[0])
            if not (
                (86 <= xmin <= 91)
                and (86 <= xmax <= 91)
                and (20 <= ymin <= 29)
                and (20 <= ymax <= 29)
            ):
                msg_ = "Please fill lat and long within the State of West Bengal."
                messages.append(msg_)
            if not ((xmax > xmin) and (ymax > ymin)):
                msg_ = "Please select NW and SE corners correctly"
                messages.append(msg_)

        if messages != []:
            messages = list(set(messages))
            raise forms.ValidationError(messages)

        return cleaned_data


class PublicForm(forms.Form):
    captcha = ReCaptchaField()
    location = SpatialLocationField(map_attrs=default_map_attrs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Row(
                    Column("location", css_class="form-group col-md-9 mb-0"),
                    Column("captcha", css_class="form-group col-md-2 mb-0"),
                ),
            ),
        )
        self.helper.form_id = "id-exampleForm"
        self.helper.form_class = "blueForms"
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Submit"))

    def clean(self):
        cleaned_data = super().clean()
        messages = []
        location = cleaned_data.get("location", "")
        if not location:
            msg_ = "Please select your location on map"
            messages.append(msg_)
        if messages != []:
            messages = list(set(messages))
            raise forms.ValidationError(messages)

        return cleaned_data


class ConfirmPublicReportForm(forms.Form):
    reference = forms.IntegerField()
    entry_date = forms.DateField(label="Ref Date")
    confirm_checkbox = forms.BooleanField(label="Confirmed by OC")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column("confirm_checkbox", css_class="form-group col-md-12 mb-0"),
                Row(
                    Column("reference", css_class="form-group col-md-12 mb-0"),
                ),
                Row(Column("entry_date", css_class="form-group col-md-12 mb-0")),
            )
        )
        self.helper.form_id = "id-exampleForm"
        self.helper.form_class = "blueForms"
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Submit"))


class DistrictForm(forms.Form):
    districts = forms.ChoiceField(choices=DISTRICTS, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column("districts", css_class="form-group col-md-12 mb-0"))
        )

        self.helper.form_id = "id-exampleForm"
        self.helper.form_class = "blueForms"
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Submit"))


class PublicReportSearchForm(forms.Form):
    telephone_of_public = forms.CharField(
        label="Public's telephone (10 digits)",
        max_length=10,
        validators=[
            RegexValidator(
                r"\d{10}",
                message="Telephone number must be 10-digit",
                code="invalid_telephone",
            ),
        ],
    )
    email_of_public = forms.EmailField(label="Public's Email")

    token_given_via_mail = forms.CharField(
        label="Token given to public via email", max_length=8
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Row(
                    Column("telephone_of_public", css_class="form-group col-md-4 mb-0"),
                    Column(
                        "email_of_public",
                        css_class="form-group col-md-4 mb-0",
                    ),
                    Column(
                        "token_given_via_mail",
                        css_class="fform-group col-md-4 mb-0",
                    ),
                )
            )
        )

        self.helper.form_method = "post"
        self.helper.form_tag = False
        self.helper.form_id = "blueForms"
        # self.helper.add_input(Submit("submit", "Search"))
