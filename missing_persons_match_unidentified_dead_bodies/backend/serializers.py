from rest_framework import serializers

from missing_persons_match_unidentified_dead_bodies.backend.models import Report
from missing_persons_match_unidentified_dead_bodies.users.models import User


# required=False, allow_blank=True, max_length=100
class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = [
            "id",
            "photo",
            "icon",
            "police_station",
            "reference",
            "entry_date",
            "name",
            "gender",
            "missing_or_found",
            "description",
            "height",
            "age",
            "guardian_name_and_address",
            "latitude",
            "longitude",
            "year",
            "matches",
        ]


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["url", "username", "email", "groups"]
