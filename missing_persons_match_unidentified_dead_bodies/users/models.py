from django.contrib.auth.models import AbstractUser
from django.db.models import (
    SET_NULL,
    BooleanField,
    CharField,
    DateTimeField,
    FloatField,
    ForeignKey,
    Model,
    TextChoices,
)
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(Model):
    created = DateTimeField(auto_now_add=True)
    modified = DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class District(TimeStampedModel):
    name = CharField(_("Name of District"), max_length=250)

    def __str__(self):
        return self.name


class PoliceStation(TimeStampedModel):
    police_stationId = CharField(_("Legacy Id"), max_length=50)
    name = CharField(_("Name of PS"), max_length=50)
    ps_with_distt = CharField(
        _("Full Name of PS"), blank=True, null=True, max_length=250
    )
    latitude = FloatField(_("Latitude of PS"), blank=True, null=True)
    longitude = FloatField(_("Longitude of PS"), blank=True, null=True)
    address = CharField(_("Address of PS"), blank=True, null=True, max_length=250)
    officer_in_charge = CharField(_("O/C of PS"), blank=True, null=True, max_length=250)
    office_telephone = CharField(
        _("Office Numberof PS"), blank=True, null=True, max_length=250
    )
    telephones = CharField(
        _("Telephone Numbers of PS"), blank=True, null=True, max_length=250
    )
    emails = CharField(_("Email ID of PS"), blank=True, null=True, max_length=250)
    district = ForeignKey(District, blank=True, null=True, on_delete=SET_NULL)

    def save(self, *args, **kwargs):
        if self.district_id:
            self.ps_with_distt = self.name + " : " + str(self.district.name)
        else:
            self.ps_with_distt = self.name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.ps_with_distt


class User(AbstractUser):
    """Default user for Crime Criminal Search."""

    #: First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore
    last_name = None  # type: ignore
    next_pk = 5000

    class Meta:
        ordering = ["pk"]

    class Categories(TextChoices):
        UNAUTHORIZED = "UNAUTHORIZED", "Unauthorized"
        VIEWER = "VIEWER", "Viewer"
        PS_ADMIN = "PS_ADMIN", "PS_Admin"
        DISTRICT_ADMIN = "DISTRICT_ADMIN", "District_Admin"
        CID_ADMIN = "CID_ADMIN", "CID_Admin"
        ADMIN = "ADMIN", "Admin"

    base_category = Categories.UNAUTHORIZED
    category = CharField(
        "Category",
        max_length=50,
        choices=Categories.choices,
        default=Categories.UNAUTHORIZED,
    )
    police_station = ForeignKey(
        PoliceStation, blank=True, null=True, on_delete=SET_NULL
    )
    district = ForeignKey(District, blank=True, null=True, on_delete=SET_NULL)
    is_oc = BooleanField(null=True)
    is_sp_or_cp = BooleanField(null=True)
    rank = CharField(_("Rank of User"), blank=True, max_length=50)
    telephone = CharField(_("Cellphone of User"), blank=True, max_length=10)

    def save(self, *args, **kwargs):
        if (not self.pk) or self.pk == 4000 or self.pk == 5000:
            self.pk = User.next_pk + 1
            User.next_pk += 1
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Get url for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})
