# from django.contrib.postgres.fields import ArrayField
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _

from missing_persons_match_unidentified_dead_bodies.users.models import PoliceStation

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
    entry_date = models.DateField()
    name = models.CharField(("Name if known"), blank=True, max_length=100)
    gender = models.CharField(("Gender"), blank=False, max_length=1)
    missing_or_found = models.CharField(("Missing Or Found"), blank=False, max_length=1)
    description = models.CharField(blank=False, max_length=500)
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
