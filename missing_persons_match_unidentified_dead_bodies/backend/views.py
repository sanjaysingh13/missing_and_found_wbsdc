# import io
import io
import json
import re
from datetime import date, timedelta

import cv2
import face_recognition
import numpy as np
# import traceback
# import requests
# from celery.result import AsyncResult
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.gis.geos import GEOSGeometry, Point
from django.contrib.postgres.search import SearchQuery, SearchVector
from django.core.paginator import Paginator
from django.db.models import Q
# from django.contrib.gis.geos import Point
# from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
# from django.core.paginator import Paginator
# from django.http import HttpResponse  # , JsonResponse, request
from django.shortcuts import redirect, render
from django.views.generic.edit import DeleteView
from fuzzywuzzy import process
from rest_framework import viewsets
from rest_framework.renderers import JSONRenderer

from missing_persons_match_unidentified_dead_bodies.backend.models import Match, Report
from missing_persons_match_unidentified_dead_bodies.backend.serializers import (
    ReportSerializer,
)
# from django.views.decorators.cache import cache_page
# from django.views.decorators.csrf import csrf_protect
from missing_persons_match_unidentified_dead_bodies.users.models import PoliceStation

from .forms import BoundedBoxSearchForm, PublicForm, ReportForm, ReportSearchForm
from .utils import generate_map_from_reports, get_reports_within_bbox, resize_image

# from .filters import ReportSearchFilter

mapbox_access_token = settings.MAP_BOX_ACCESS_TOKEN
gmap_access_token = settings.GOOGLE_MAPS_API

s3_file_pattern = re.compile(r".*https.*")
pk_pattern = re.compile(r"\$primary_key=(\d+)$")
root = (
    "/Users/sanjaysingh/non_icloud/"
    + "missing_persons_match_unidentified_dead_bodies/"
    + "missing_persons_match_unidentified_dead_bodies/media/"
)


def match_encodings(report):
    face_encoding = report.face_encoding
    face_encoding = json.loads(face_encoding)
    face_encoding = np.array(face_encoding, dtype="float64")
    gender = report.gender
    missing_or_found = report.missing_or_found
    height = report.height
    # entry_date = report.entry_date
    if missing_or_found == "M":
        required = "F"
    else:
        required = "M"
    reports_under_consideration = Report.objects.filter(
        gender=gender, missing_or_found=required
    )
    if height:
        reports_under_consideration = reports_under_consideration.filter(
            height__gte=height - 10, height__lte=height + 10
        )
    face_encodings = []
    ids = []
    for report in reports_under_consideration:
        if report.face_encoding:
            face_encodings.append(
                np.array(json.loads(report.face_encoding), dtype="float64")
            )
            ids.append(report.pk)
    if face_encodings != []:
        all_matches = face_recognition.compare_faces(
            face_encodings, face_encoding, tolerance=0.5
        )
        matched_images = [id_ for idx, id_ in enumerate(ids) if all_matches[idx]]
    else:
        matched_images = None
    return matched_images


@login_required
@permission_required("users.add_user", raise_exception=True)
def upload_photo(request):
    template_name = "backend/photo_upload_form.html"
    if request.method == "GET":
        reportsform = ReportForm(request.GET or None)
    elif request.method == "POST":
        reportsform = ReportForm(request.POST, request.FILES)
        if reportsform.is_valid():
            files = request.FILES.getlist("photo")
            cleaned_data = reportsform.cleaned_data
            reference = cleaned_data.get("reference", "")
            entry_date = cleaned_data.get("entry_date", "")
            name = cleaned_data.get("name", "")
            gender = cleaned_data.get("gender", "")
            age = cleaned_data.get("age", "")
            guardian_name_and_address = cleaned_data.get(
                "guardian_name_and_address", ""
            )
            missing_or_found = cleaned_data.get("missing_or_found", "")
            height = cleaned_data.get("height", "")
            description = cleaned_data.get("description", "")
            latitude = cleaned_data.get("latitude", "")
            longitude = cleaned_data.get("longitude", "")
            police_station_with_distt = cleaned_data.get(
                "police_station_with_distt", ""
            )
            location = cleaned_data.get("location", "")
            # Encoding face
            for f in files:
                resized_image, icon = resize_image(f, 600, 64)
                report = Report(
                    photo=resized_image,
                    icon=icon,
                    reference=reference,
                    entry_date=entry_date,
                    name=name,
                    gender=gender,
                    missing_or_found=missing_or_found,
                    height=height,
                    description=description,
                    latitude=latitude,
                    longitude=longitude,
                    age=age,
                    guardian_name_and_address=guardian_name_and_address,
                )
                police_station = PoliceStation.objects.get(
                    ps_with_distt=police_station_with_distt.strip()
                )
                report.police_station = police_station
                img = cv2.imdecode(
                    np.fromstring(resized_image.read(), np.uint8),
                    cv2.IMREAD_UNCHANGED,
                )
                _, img_encoded = cv2.imencode(".jpeg", img)
                memory_file_output = io.BytesIO()
                memory_file_output.write(img_encoded)
                memory_file_output.seek(0)
                image = face_recognition.load_image_file(memory_file_output)
                face_encoding = face_recognition.face_encodings(image)
                if len(face_encoding) != 0:
                    face_encoding = face_encoding[0]
                    face_encoding = json.dumps(face_encoding.tolist())
                    report.face_encoding = face_encoding
                report.year = str(entry_date.year)[-2:]
                if location:
                    report.location = location
                else:
                    report.location = Point(longitude, latitude)
                report.save()
                return redirect("backend:view_report", object_id=report.id)
    return render(
        request,
        template_name,
        {"reportsform": reportsform, "mapbox_access_token": mapbox_access_token},
    )


def view_report(request, object_id):
    report = Report.objects.get(id=object_id)
    context = {}
    reports = []
    if report.face_encoding:
        matched_reports = match_encodings(report)
        if matched_reports:
            reports = Report.objects.filter(pk__in=matched_reports).only(
                "pk", "photo", "description", "entry_date", "name", "police_station"
            )
            if report.missing_or_found == "M":
                for report_found in reports:
                    if not Match.objects.filter(
                        report_missing=report, report_found=report_found
                    ).exists():
                        match = Match(report_missing=report, report_found=report_found)
                        match.save()
            else:
                for report_missing in reports:
                    if not Match.objects.filter(
                        report_missing=report_missing, report_found=report
                    ).exists():
                        match = Match(
                            report_missing=report_missing, report_found=report
                        )
                        match.save()
    context["report"] = report
    paginator = Paginator(reports, 2)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context["matches"] = page_obj
    template_name = "backend/report_detail.html"
    return render(request, template_name, context)


@login_required
@permission_required("users.add_user", raise_exception=True)
def report_search(request):
    template_name = "backend/report_search.html"

    if request.method == "GET":
        form = ReportSearchForm(
            initial={
                "full_text_search_type": 0,
                "missing_or_found": "All",
                "gender": "All",
                "map_or_list": "L",
            }
        )
    elif request.method == "POST":
        form = ReportSearchForm(request.POST)
        print("hello")
        if form.is_valid():
            print("valid")
            cleaned_data = form.cleaned_data
            keywords = cleaned_data.get("keywords", "")
            full_text_search_type = int(cleaned_data.get("full_text_search_type", ""))
            districts = cleaned_data.get("districts", "")
            ps_list = cleaned_data.get("ps_list", "")
            min_date = cleaned_data.get("min_date", "")
            max_date = cleaned_data.get("max_date", "")
            advanced_search_report = cleaned_data.get("advanced_search_report", "")
            missing_or_found = cleaned_data.get("missing_or_found", "")
            gender = cleaned_data.get("gender", "")
            latitude = cleaned_data.get("latitude", "")
            longitude = cleaned_data.get("longitude", "")
            distance = cleaned_data.get("distance", "")
            location = cleaned_data.get("location", "")
            map_or_list = cleaned_data.get("map_or_list", "")
            if advanced_search_report:
                if not min_date:
                    min_date = date.today() - timedelta(days=30)
                if not max_date:
                    max_date = date.today()
                query_object = Q(entry_date__gte=min_date) & Q(entry_date__lte=max_date)

                if districts != "Null":
                    query_object = query_object & Q(
                        police_station__district__in=[int(districts)]
                    )
                    districts = districts
                if ps_list != "":
                    police_stations = ps_list.split(", ")
                    police_stations = [int(ps.strip()) for ps in police_stations if ps]
                    police_stations = list(filter(None, police_stations))
                    query_object = query_object & Q(
                        police_station__pk__in=police_stations
                    )
                if missing_or_found != "All":
                    query_object = query_object & Q(missing_or_found=missing_or_found)
                if gender != "All":
                    query_object = query_object & Q(gender=gender)
                given_location = None
                if location:
                    given_location = location
                elif latitude != "":
                    given_location = GEOSGeometry(
                        f"POINT({longitude} {latitude})", srid=4326
                    )
                if given_location:
                    distance = distance * 1000
                    query_object = query_object & Q(
                        location__dwithin=(given_location, distance)
                    )
                reports = Report.objects.filter(query_object)
                if keywords != "":
                    if full_text_search_type == 0:
                        query = SearchQuery(keywords, search_type="websearch")
                        vector = SearchVector("description", config="english")
                        reports = reports.annotate(search=vector).filter(search=query)
                    elif full_text_search_type == 1:
                        choices = [
                            r.description + f" $primary_key={r.pk}" for r in reports
                        ]
                        results = process.extract(keywords, choices, limit=10)
                        results = [result for (result, score) in results if score > 50]
                        print(results)
                        results = [
                            int(pk_pattern.search(string).group(1))
                            for string in results
                        ]
                        print(results)
                        reports = reports.filter(pk__in=results)
                # testing serialisation
                serializer = ReportSerializer(reports, many=True)
                print(JSONRenderer().render(serializer.data))

                reports = reports.only(
                    "id",
                    "name",
                    "description",
                    "photo",
                    "icon",
                    "entry_date",
                    "age",
                    "guardian_name_and_address",
                    "height",
                    "location",
                    "gender",
                    "missing_or_found",
                    "police_station",
                )
                print(f"-------{len(reports)}------")
                if map_or_list == "L":
                    reports = reports.values()
                    report_list = []
                    for report in reports:
                        rep = Report.objects.get(pk=report["id"])
                        report["matched"] = (
                            Match.objects.filter(report_found=rep).exists()
                            or Match.objects.filter(report_missing=rep).exists()
                        )
                        report["photo"] = Report.objects.get(pk=report["id"]).photo.url
                        report["ps"] = rep.police_station.ps_with_distt
                        report["oc"] = rep.police_station.officer_in_charge
                        report["tel"] = rep.police_station.telephones
                        report_list.append(report)
                    reports = report_list
                    context = {}
                    context["title"] = "Advanced Search Results"
                    paginator = Paginator(reports, 5)
                    page_number = request.GET.get("page")
                    page_obj = paginator.get_page(page_number)
                    context["reports"] = page_obj
                    template_name = "backend/advanced_report_search_results.html"
                    return render(request, template_name, context)
                else:
                    report_dicts = generate_map_from_reports(reports)
                    template_name = "backend/reports_map.html"
                    context = {}
                    context["mapbox_access_token"] = mapbox_access_token
                    context["reports_json"] = report_dicts
                    if given_location:
                        context["location"] = json.dumps(
                            [given_location.y, given_location.x]
                        )
                    else:
                        context["location"] = json.dumps(None)
                        print(context["location"])
                    return render(request, template_name, context)
                return render(request, template_name, context)
            else:
                reference = int(cleaned_data.get("ref_no", ""))
                entry_date = cleaned_data.get("ref_date", "")
                ps_with_distt = cleaned_data.get("police_station_with_distt", "")
                year = cleaned_data.get("ref_year", "")
                # Start with a Q object that matches all Report objects
                query = Q()

                # Add a filter for reference, if provided
                if reference:
                    query &= Q(reference=reference)

                # Add a filter for police station, if provided
                if ps_with_distt:
                    query &= Q(police_station__ps_with_distt=ps_with_distt)

                # Add a filter for entry date, if provided
                if entry_date:
                    query &= Q(entry_date=entry_date)

                # Add a filter for year, if provided
                if year:
                    query &= Q(year=year)

                # Use the Q object to filter the Report objects
                reports = Report.objects.filter(query)
                if not reports.exists():
                    context = {}
                    context["form"] = form
                    context["mapbox_access_token"] = mapbox_access_token
                    context["form_title"] = "Basic and Advanced Search for Reports"
                    context["title"] = "Report Search"
                    messages.info(request, "No report found")
                    return render(request, template_name, context)
                else:
                    return redirect("backend:view_report", reports[0].pk)
    context = {}
    context["form"] = form
    context["mapbox_access_token"] = mapbox_access_token
    context["form_title"] = "Basic and Advanced Search for Reports"
    context["title"] = "Report Search"
    return render(request, template_name, context)


# New bounded-box search interface:
@login_required
@permission_required("users.add_user", raise_exception=True)
def bounded_box_search(request):
    template = "backend/bounded_box_search.html"
    if request.method == "GET":
        form = BoundedBoxSearchForm(
            initial={
                "gender": "F",
                "min_date": date.today() - timedelta(days=30),
                "max_date": date.today(),
                "lines": "waterlines",
            }
        )
    elif request.method == "POST":
        form = BoundedBoxSearchForm(request.POST)
        if form.is_valid():
            print("valid")
            cleaned_data = form.cleaned_data
            print(cleaned_data)
            gender = cleaned_data.get("gender", "")
            min_date = cleaned_data.get("min_date", "")
            max_date = cleaned_data.get("max_date", "")
            north_west_location = cleaned_data.get("north_west_location", "").split(",")
            xmin = float(north_west_location[1])
            ymax = float(north_west_location[0])
            south_east_location = cleaned_data.get("south_east_location", "").split(",")
            xmax = float(south_east_location[1])
            ymin = float(south_east_location[0])
            lines = cleaned_data.get("lines", "")
            print(xmin, ymin, xmax, ymax, lines)
            bounded_box_reports = get_reports_within_bbox(xmin, ymin, xmax, ymax, lines)
            print(bounded_box_reports)
            bounded_box_reports = bounded_box_reports.filter(
                entry_date__gte=min_date,
                entry_date__lte=max_date,
                gender=gender,
                missing_or_found="F",
            )
            bounded_box_reports = generate_map_from_reports(bounded_box_reports)
            if bounded_box_reports == []:
                messages.info(request, "No report found")
                context = {}
                context["form"] = form
                context["form_title"] = "Bounded Box Search"
                context["title"] = "Bounded Box Search"
                context["mapbox_access_token"] = mapbox_access_token
                return render(request, template, context)

            context = {}
            template = "backend/reports_map.html"
            context["mapbox_access_token"] = mapbox_access_token
            context["reports_json"] = bounded_box_reports
            context["location"] = json.dumps(None)
            context["title"] = "Curated Search Results"
            return render(request, template, context)
        else:
            context = {}
            context["form"] = form
            context["form_title"] = "Bounded Box Search"
            context["title"] = "Bounded Box Search"
            context["mapbox_access_token"] = mapbox_access_token
            return render(request, template, context)
    context = {}
    context["form"] = form
    context["mapbox_access_token"] = mapbox_access_token
    context["form_title"] = "Curated Search for Dead Bodies along river/rail/road"
    context["title"] = "Curated Search River/Rail/Road"
    return render(request, template, context)


@login_required
@permission_required("users.add_user", raise_exception=True)
def matches(request):
    matches = Match.objects.all().order_by("-mail_sent").values()
    matched_reports = [
        (
            Report.objects.get(pk=match["report_missing_id"]),
            Report.objects.get(pk=match["report_found_id"]),
        )
        for match in matches
    ]
    matched_reports = [
        (
            (
                report_missing.photo,
                report_missing.description,
                report_missing.entry_date,
                report_missing.name,
                report_missing.police_station,
                report_missing.pk,
            ),
            (
                report_found.photo,
                report_found.description,
                report_found.entry_date,
                report_found.name,
                report_found.police_station,
                report_found.pk,
            ),
        )
        for (report_missing, report_found) in matched_reports
    ]
    paginator = Paginator(matched_reports, 2)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {}
    context["matches"] = page_obj
    template_name = "backend/matches.html"
    return render(request, template_name, context)


# @login_required
# @permission_required("users.delete_user", raise_exception=True)
class ReportDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    # specify the model you want to use
    model = Report
    permission_required = "users.delete_user"
    template_name = "backend/report_confirm_delete.html"
    # can specify success url
    # url to redirect after successfully
    # deleting object
    success_url = "/"


# class ReportSerializer(serializers.HyperlinkedModelSerializer):
#     url = serializers.HyperlinkedIdentityField(view_name="backend:view_report")
#     class Meta:
#         model = Report
#         fields = ["url", "name", "missing_or_found", "gender"]


# ViewSets define the view behavior.
class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all().order_by("name")
    serializer_class = ReportSerializer


# class ReportSearchViewSet(viewsets.ModelViewSet):
#     queryset = Report.objects.all()
#     serializer_class = SearchReportSerializer
#     filter_class = ReportSearchFilter
#     filter_backends = (filters.SearchFilter, filters.OrderingFilter,)
#     search_fields = (
#         'districts',
#         'keywords',
#         'full_text_search_type',
#         'missing_or_found',
#         'gender',
#         'min_date',
#         'max_date',
#         'ps_list',
#         'location',
#         'distance',
#         'map_or_list'
#     )
#     def get(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data)
#         serializer,data['search_results'] = self.search()
#         return Response(serializer.data)
#     def search(self):
#         # search logic
#         return search_results


def public(request):
    template_name = "backend/public.html"
    context = {}
    if request.method == "GET":
        form = PublicForm()

    elif request.method == "POST":
        form = PublicForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            location = cleaned_data.get("location", "")
            min_date = date.today() - timedelta(days=90)
            max_date = date.today()
            query_object = Q(entry_date__gte=min_date) & Q(entry_date__lte=max_date)
            query_object = query_object & Q(missing_or_found="M")
            distance = 50 * 1000
            query_object = query_object & Q(location__dwithin=(location, distance))
            reports = Report.objects.filter(query_object)
            reports = reports.only(
                "id",
                "name",
                "description",
                "photo",
                "icon",
                "entry_date",
                "age",
                "guardian_name_and_address",
                "height",
                "location",
                "gender",
                "missing_or_found",
                "police_station",
            )
            report_dicts = generate_map_from_reports(reports)
            template_name = "backend/reports_map.html"
            context = {}
            context["mapbox_access_token"] = mapbox_access_token
            context["reports_json"] = report_dicts
            context["location"] = json.dumps([location.y, location.x])
            return render(request, template_name, context)
    context["form"] = form
    context["mapbox_access_token"] = mapbox_access_token
    context["form_title"] = "Missing Persons Near You"
    context["title"] = "Area for River Search"
    return render(request, template_name, context)
