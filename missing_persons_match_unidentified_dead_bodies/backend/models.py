# from django.contrib.postgres.fields import ArrayField

from django.contrib.gis.db import models
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.urls import reverse
# from django.core.files import File
from django.utils.translation import gettext_lazy as _

from missing_persons_match_unidentified_dead_bodies.users.models import (
    PoliceStation,
    User,
)

# from PIL import Image


# from mapbox_location_field.spatial.models import SpatialLocationField


class TimeStampedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Report(TimeStampedModel):
    photo = models.FileField()
    icon = models.FileField(null=True)
    police_station = models.ForeignKey(
        PoliceStation, blank=True, null=True, on_delete=models.SET_NULL
    )
    reference = models.IntegerField("PS Reference")
    entry_date = models.DateField(db_index=True)
    name = models.CharField(("Name if known"), blank=True, null=True, max_length=100)
    gender = models.CharField(("Gender"), blank=True, null=True, max_length=1)
    missing_or_found = models.CharField(("Missing Or Found"), blank=False, max_length=1)
    description = models.CharField(blank=False, max_length=500)
    description_search_vector = SearchVectorField(null=True)
    height = models.IntegerField()
    age = models.IntegerField()
    guardian_name_and_address = models.CharField(
        ("Name if known"), blank=True, null=True, max_length=300
    )
    face_encoding = models.CharField(blank=True, null=True, max_length=4000)
    latitude = models.FloatField(_("Latitude of Event"), blank=True, null=True)
    longitude = models.FloatField(_("Longitude of Event"), blank=True, null=True)
    location = models.PointField(srid=4326, geography=True, null=True)
    # spatial_location = SpatialLocationField()
    year = models.CharField(blank=True, max_length=2)
    reconciled = models.BooleanField(default=False)
    matches = models.ManyToManyField("self", related_name="matched_by", through="Match")
    uploaded_by = models.ForeignKey(
        User, blank=True, null=True, on_delete=models.SET_NULL
    )

    class Meta:
        indexes = (GinIndex(fields=["description_search_vector"]),)  # add index
        constraints = [
            models.UniqueConstraint(
                fields=["police_station", "reference", "entry_date"],
                name="unique_report",
            )
        ]

    def __str__(self):
        if self.missing_or_found == "M":
            person = "Missing : "
        else:
            person = "Found : "
        if self.name:
            person = person + self.name
        if self.guardian_name_and_address:
            person = person + " " + self.guardian_name_and_address
        if self.entry_date:
            person = person + " dt. " + self.entry_date.strftime("%d,%b,%Y")
        if self.police_station:
            person = person + " P.S. " + self.police_station.name
        return person


class PublicReport(TimeStampedModel):
    photo = models.FileField()
    telephone_of_missing = models.CharField(max_length=10)
    telephone_of_reporter = models.CharField(max_length=10)
    email_of_reporter = models.EmailField()
    icon = models.FileField(null=True)
    police_station = models.ForeignKey(
        PoliceStation, blank=True, null=True, on_delete=models.SET_NULL
    )
    entry_date = models.DateField(null=True)
    missing_or_found = models.CharField(("Missing Or Found"), blank=False, max_length=1)

    name = models.CharField(("Name"), max_length=100)
    gender = models.CharField(("Gender"), blank=True, null=True, max_length=1)
    description = models.CharField(blank=False, max_length=500)
    description_search_vector = SearchVectorField(null=True)
    height = models.IntegerField()
    age = models.IntegerField()
    guardian_name_and_address = models.CharField(
        ("Name if known"), blank=True, null=True, max_length=300
    )
    face_encoding = models.CharField(blank=True, null=True, max_length=4000)
    location = models.PointField(srid=4326, geography=True, null=True)
    # spatial_location = SpatialLocationField()
    token = models.CharField(max_length=8)
    year = models.CharField(blank=True, max_length=2)
    reconciled = models.BooleanField(default=False)

    class Meta:
        indexes = (GinIndex(fields=["description_search_vector"]),)  # add index

    def __str__(self):
        person = "Missing : "
        if self.name:
            person = person + self.name
        if self.guardian_name_and_address:
            person = person + " " + self.guardian_name_and_address
        if self.entry_date:
            person = person + " dt. " + self.entry_date.strftime("%d,%b,%Y")
        if self.police_station:
            person = person + " P.S. " + self.police_station.name
        return person

    # def save(self, *args, **kwargs): # Will use this later in CCS
    #     # Open the uploaded photo
    #     with Image.open(self.photo) as img:
    #         # Create a thumbnail
    #         img.thumbnail((64, 64))

    #         # Create a BytesIO object to save the thumbnail
    #         thumb_io = BytesIO()
    #         img.save(thumb_io, "JPEG")

    #         # Seek to the beginning of the BytesIO object
    #         thumb_io.seek(0)

    #         # Save the thumbnail to the icon field
    #         self.icon.save(self.photo.name, File(thumb_io), save=False)
    #         super().save(*args, **kwargs)


class AdvancedReportSearch(TimeStampedModel):
    keywords = models.CharField(max_length=100, null=True)
    full_text_search_type = models.IntegerField(null=True)
    missing_or_found = models.CharField(max_length=3, null=True)
    gender = models.CharField(max_length=3, null=True)
    latitude = models.CharField(max_length=20, null=True)
    longitude = models.CharField(max_length=20, null=True)
    location = models.PointField(srid=4326, geography=True, null=True)
    distance = models.IntegerField(null=True)
    ps_list = models.CharField(max_length=500, null=True)
    districts = models.CharField(max_length=200, null=True)
    min_date = models.DateField(null=True)
    max_date = models.DateField(null=True)

    def get_absolute_url(self):
        return reverse("backend:advanced_report_search", kwargs={"pk": self.pk})


class Match(TimeStampedModel):
    report_missing = models.ForeignKey(
        Report, on_delete=models.CASCADE, related_name="report_missing"
    )
    report_found = models.ForeignKey(
        Report, on_delete=models.CASCADE, related_name="report_found"
    )
    mail_sent = models.DateField(null=True)


class PublicReportMatch(TimeStampedModel):
    report_missing = models.ForeignKey(
        "PublicReport", on_delete=models.CASCADE, related_name="public_report_missing"
    )
    report_found = models.ForeignKey(
        Report, on_delete=models.CASCADE, related_name="public_report_found"
    )
    mail_sent = models.DateField(null=True)


class MitRailLines(models.Model):
    f_code = models.CharField(max_length=255, null=True)
    fco = models.IntegerField()
    exs = models.IntegerField()
    loc = models.IntegerField()
    soc = models.CharField(max_length=255, null=True)
    geom = models.MultiLineStringField(srid=4326, geography=True)


class MitWaterLines(models.Model):
    f_code = models.CharField(max_length=255, null=True)
    hyc = models.IntegerField()
    lit = models.IntegerField()
    nam = models.CharField(max_length=255, null=True)
    soc = models.CharField(max_length=255, null=True)
    geom = models.MultiLineStringField(srid=4326, geography=True)


class MitRoadLines(models.Model):
    f_code = models.CharField(max_length=255, null=True)
    acc = models.IntegerField()
    exs = models.IntegerField()
    rst = models.IntegerField()
    med = models.IntegerField()
    rtt = models.IntegerField()
    rsu = models.IntegerField()
    loc = models.IntegerField()
    soc = models.CharField(max_length=255, null=True)
    geom = models.MultiLineStringField(srid=4326, geography=True)


class EmailRecord(models.Model):
    data = models.CharField(max_length=4000)
    email = models.CharField(max_length=100)
