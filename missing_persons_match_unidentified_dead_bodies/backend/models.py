# from django.contrib.postgres.fields import ArrayField

from django.contrib.gis.db import models
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
# from django.core.files import File
from django.utils.translation import gettext_lazy as _

from missing_persons_match_unidentified_dead_bodies.users.models import PoliceStation

# from PIL import Image


# from mapbox_location_field.spatial.models import SpatialLocationField


class TimeStampedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Report(TimeStampedModel):
    photo = models.FileField()
    icon = models.FileField(blank=True)
    police_station = models.ForeignKey(
        PoliceStation, blank=True, null=True, on_delete=models.SET_NULL
    )
    reference = models.IntegerField("PS Reference")
    entry_date = models.DateField()
    name = models.CharField(("Name if known"), blank=True, max_length=100)
    gender = models.CharField(("Gender"), blank=False, max_length=1)
    missing_or_found = models.CharField(("Missing Or Found"), blank=False, max_length=1)
    description = models.CharField(blank=False, max_length=500)
    description_search_vector = SearchVectorField(null=True)
    height = models.IntegerField()
    age = models.IntegerField()
    guardian_name_and_address = models.CharField(
        ("Name if known"), blank=True, max_length=300
    )
    face_encoding = models.CharField(blank=True, max_length=4000)
    latitude = models.FloatField(_("Latitude of Event"), blank=True, null=True)
    longitude = models.FloatField(_("Longitude of Event"), blank=True, null=True)
    location = models.PointField(srid=4326, geography=True, null=True)
    # spatial_location = SpatialLocationField()
    year = models.CharField(blank=True, max_length=2)
    matches = models.ManyToManyField("self", related_name="matched_by", through="Match")

    class Meta:
        indexes = (GinIndex(fields=["description_search_vector"]),)  # add index

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


class Match(TimeStampedModel):
    report_missing = models.ForeignKey(
        Report, on_delete=models.CASCADE, related_name="report_missing"
    )
    report_found = models.ForeignKey(
        Report, on_delete=models.CASCADE, related_name="report_found"
    )
    mail_sent = models.DateField(null=True)
