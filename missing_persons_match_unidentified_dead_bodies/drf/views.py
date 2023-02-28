# from django.contrib.auth.models import Group
import re
from datetime import date, datetime, timedelta

from django.contrib.gis.geos import GEOSGeometry
from django.contrib.postgres.search import SearchQuery, SearchVector
from django.db.models import Q
from fuzzywuzzy import process
from rest_framework import permissions, viewsets
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from missing_persons_match_unidentified_dead_bodies.backend.models import Report
from missing_persons_match_unidentified_dead_bodies.drf.serializers import (
    ReportSerializer,
    UserSerializer,
)
from missing_persons_match_unidentified_dead_bodies.users.models import User

pk_pattern = re.compile(r"\$primary_key=(\d+)$")


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


@api_view(["POST"])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def search_reports(request):
    print(request.data)
    min_date = request.data.get("min_date")
    max_date = request.data.get("max_date")
    keywords = request.data.get("keywords")
    full_text_search_type = int(request.data.get("full_text_search_type"))
    districts = request.data.get("districts")
    ps_list = request.data.get("ps_list")
    min_date = request.data.get("min_date")
    max_date = request.data.get("max_date")
    # advanced_search_report = request.data.get("advanced_search_report")
    missing_or_found = request.data.get("missing_or_found")
    if missing_or_found == "Missing":
        missing_or_found = "M"
    elif missing_or_found == "Found":
        missing_or_found = "F"
    elif missing_or_found == "Unidentified":
        missing_or_found = "U"
    gender = request.data.get("gender")
    if gender == "Male":
        gender = "M"
    elif gender == "Female":
        gender = "F"
    latitude = request.data.get("latitude")
    longitude = request.data.get("longitude")
    distance = request.data.get("distance")
    location = request.data.get("location")

    # Use the parsed parameters to search for reports
    min_date = datetime.strptime(min_date, "%Y-%m-%d").date()
    max_date = datetime.strptime(max_date, "%Y-%m-%d").date()
    if not min_date:
        min_date = date.today() - timedelta(days=30)
    if not max_date:
        max_date = date.today()
    query_object = (
        Q(entry_date__gte=min_date) & Q(entry_date__lte=max_date) & Q(reconciled=False)
    )

    if districts != "Null":
        query_object = query_object & Q(police_station__district__in=[int(districts)])
        districts = districts
    if ps_list != "":
        police_stations = ps_list.split(",")
        police_stations = [int(ps.strip()) for ps in police_stations if ps]
        police_stations = list(filter(None, police_stations))
        query_object = query_object & Q(police_station__pk__in=police_stations)
    if missing_or_found != "All":
        query_object = query_object & Q(missing_or_found=missing_or_found)
    if gender != "All":
        query_object = query_object & Q(gender=gender)
    given_location = None
    if location:
        given_location = location
    elif latitude != "":
        given_location = GEOSGeometry(f"POINT({longitude} {latitude})", srid=4326)
    if given_location:
        distance = distance * 1000
        query_object = query_object & Q(location__dwithin=(given_location, distance))
    reports = Report.objects.filter(query_object)
    if keywords != "":
        if full_text_search_type == 0:
            query = SearchQuery(keywords, search_type="websearch")
            vector = SearchVector("description", config="english")
            reports = reports.annotate(search=vector).filter(search=query)
        elif full_text_search_type == 1:
            results = []
            choices = [r.description + f" $primary_key={r.pk}" for r in reports]
            results = process.extract(keywords, choices, limit=10)
            results = [result for (result, score) in results if score > 50]
            results = [int(pk_pattern.search(string).group(1)) for string in results]
            reports = reports.filter(pk__in=results)
    serializer = ReportSerializer(reports, many=True)
    print(JSONRenderer().render(serializer.data))

    # ...

    # Return the results in a JSON format
    return Response({"reports": serializer.data})
