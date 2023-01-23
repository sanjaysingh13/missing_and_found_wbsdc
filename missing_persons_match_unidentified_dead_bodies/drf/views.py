# from django.contrib.auth.models import Group
from rest_framework import viewsets

from missing_persons_match_unidentified_dead_bodies.backend.models import Report
from missing_persons_match_unidentified_dead_bodies.drf.serializers import (
    ReportSerializer,
)


class ReportViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = Report.objects.all().order_by("name")
    serializer_class = ReportSerializer
