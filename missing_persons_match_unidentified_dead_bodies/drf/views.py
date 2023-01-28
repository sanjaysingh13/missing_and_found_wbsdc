# from django.contrib.auth.models import Group
from rest_framework import permissions, viewsets

from missing_persons_match_unidentified_dead_bodies.backend.models import Report
from missing_persons_match_unidentified_dead_bodies.drf.serializers import (
    ReportSerializer,
    UserSerializer,
)
from missing_persons_match_unidentified_dead_bodies.users.models import User


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


# ViewSets define the view behavior.
class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all().order_by("name")
    serializer_class = ReportSerializer
