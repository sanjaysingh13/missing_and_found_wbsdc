from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from missing_persons_match_unidentified_dead_bodies.users.forms import (  # ,UserChangeForm
    UserCreationForm,
)

from .models import District, PoliceStation

User = get_user_model()

# user_permissions.add(permission, permission, ...) groups.set([group_list])


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    def has_add_permission(self, request, obj=None):
        if not request.user.category == "ADMIN" or request.user.category == "CID_ADMIN":
            return False
        return True

    def get_form(self, request, obj=None, **kwargs):
        # form = UserChangeForm
        form = super().get_form(request, obj, **kwargs)
        is_superuser = request.user.is_superuser
        disabled_fields = set()  # type: Set[str]

        if not is_superuser:
            disabled_fields |= {
                "is_superuser",
                "user_permissions",
            }

        if not is_superuser and obj is not None and obj == request.user:
            disabled_fields |= {
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            }
        if not (request.user.category == "ADMIN" or request.user.category == "CID_ADMIN"):
            disabled_fields |= {
                "is_staff",
            }

        for f in disabled_fields:
            if f in form.base_fields:
                form.base_fields[f].disabled = True

        return form

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if request.user.category == "DISTRICT_ADMIN":
            if db_field.name == "police_station":
                kwargs["queryset"] = PoliceStation.objects.filter(
                    district=request.user.district
                ).order_by("name")
            if db_field.name == "district":
                kwargs["queryset"] = District.objects.filter(
                    name=request.user.district.name
                )
        elif request.user.category == "CID_ADMIN" or request.user.category == "ADMIN":
            if db_field.name == "police_station":
                kwargs["queryset"] = PoliceStation.objects.all().order_by("name")
            if db_field.name == "district":
                kwargs["queryset"] = District.objects.all().order_by("name")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "category":
            kwargs["choices"] = (
                ("UNAUTHORIZED", "Unauthorized"),
                ("PS_ADMIN", "PS_Admin"),
                ("VIEWER", "Viewer"),
            )
            if request.user.category == "DISTRICT_ADMIN":
                kwargs["choices"] = kwargs["choices"]
            if request.user.category == "CID_ADMIN":
                kwargs["choices"] += (("DISTRICT_ADMIN", "District_Admin"),)
            if request.user.is_superuser:
                kwargs["choices"] += (
                    ("DISTRICT_ADMIN", "District_Admin"),
                    ("CID_ADMIN", "CID_Admin"),
                    ("ADMIN", "Admin"),
                )
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        elif request.user.category == "CID_ADMIN":
            return qs.exclude(category="ADMIN")
        elif request.user.category == "DISTRICT_ADMIN":
            return qs.filter(district=request.user.district)

    # def save_model(self,request,obj,form,change):
    #     print(form.cleaned_data)
    #     if obj.category == "DISTRICT_ADMIN":
    #         distt_admin = Group.objects.get(name='Distt_Admin')
    #         print(distt_admin.id)
    #         obj.groups.add(distt_admin)
    #         obj.save()
    #     super().save_model(request,obj,form,change)

    add_form = UserCreationForm
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("name", "email")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "category",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "user_permissions",
                    "police_station",
                    "is_oc",
                    "district",
                    "is_sp_or_cp",
                    "rank",
                    "telephone",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    list_display = ["username", "name", "email", "district"]
    search_fields = ["username"]


class PoliceStationAdmin(admin.ModelAdmin):
    fields = (
        "police_stationId",
        "name",
        "latitude",
        "longitude",
        "address",
        "officer_in_charge",
        "office_telephone",
        "telephones",
        "emails",
        "district",
    )
    list_display = ["name", "district"]
    search_fields = ["name"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.category == "CID_ADMIN":
            return qs
        elif request.user.category == "DISTRICT_ADMIN":
            return qs.filter(district=request.user.district)
        elif request.user.category == "PS_ADMIN":
            return qs.filter(id=request.user.police_station.id)

    def get_form(self, request, obj=None, **kwargs):
        # form = UserChangeForm
        form = super().get_form(request, obj, **kwargs)
        is_superuser = request.user.is_superuser
        disabled_fields = set()  # type: Set[str]

        if not (is_superuser or request.user.category == "CID_ADMIN"):
            disabled_fields |= {
                "police_stationId",
                "name",
            }
        for f in disabled_fields:
            if f in form.base_fields:
                form.base_fields[f].disabled = True

        return form


admin.site.register(PoliceStation, PoliceStationAdmin)


class DistrictAdmin(admin.ModelAdmin):
    fields = ("name",)


admin.site.register(District, DistrictAdmin)
