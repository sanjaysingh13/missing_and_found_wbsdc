# import io
import json
import re
import urllib

import cv2
import face_recognition
import numpy as np
# import traceback
# import requests
# from celery.result import AsyncResult
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.gis.geos import GEOSGeometry, Point
from django.core.paginator import Paginator
from django.db.models import Q
# from django.contrib.gis.geos import Point
# from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
# from django.core.paginator import Paginator
# from django.http import HttpResponse  # , JsonResponse, request
from django.shortcuts import redirect, render

from missing_persons_match_unidentified_dead_bodies.backend.models import Report
# from django.views.decorators.cache import cache_page
# from django.views.decorators.csrf import csrf_protect
from missing_persons_match_unidentified_dead_bodies.users.models import PoliceStation

from .forms import ReportForm, ReportSearchForm

mapbox_access_token = settings.MAP_BOX_ACCESS_TOKEN

s3_file_pattern = re.compile(r".*https.*")
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
    # reports_under_consideration = reports_under_consideration.filter(
    # entry_date__gte=entry_date-10, entry_date__lte=entry_date+90)
    face_encodings = [
        np.array(json.loads(report.face_encoding), dtype="float64")
        for report in reports_under_consideration
    ]
    ids = [report.pk for report in reports_under_consideration]
    all_matches = face_recognition.compare_faces(
        face_encodings, face_encoding, tolerance=0.5
    )
    matched_images = [id_ for idx, id_ in enumerate(ids) if all_matches[idx]]
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
            entry_date = cleaned_data.get("entry_date", "")
            name = cleaned_data.get("name", "")
            gender = cleaned_data.get("gender", "")
            age = cleaned_data.get("age", "")
            guardian_name_and_address = cleaned_data.get("guardian_name_and_address", "")
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
                report = Report(
                    photo=f,
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
                report.save()
                url = report.photo.url
                if not s3_file_pattern .search(url):
                    root = (
                        "/Users/sanjaysingh/non_icloud/"
                        + "missing_persons_match_unidentified_dead_bodies/"
                        + "missing_persons_match_unidentified_dead_bodies/media/"
                    )

                    url = root + url
                    img = face_recognition.load_image_file(url)
                    face_encoding = face_recognition.face_encodings(img)
                else:
                    url = url.replace("ccs-django", "ccs-django-uploads")
                    print(f"URL IS {url}")
                    req = urllib.request.urlopen(url)
                    arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
                    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
                    cv2.imwrite("tmp.jpg", img)
                    image = face_recognition.load_image_file("tmp.jpg")
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
    matched_reports = match_encodings(report)
    reports = Report.objects.filter(pk__in=matched_reports)
    context["report"] = report
    paginator = Paginator(reports, 2)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context["matches"] = page_obj
    template_name = "backend/report_detail.html"
    return render(request, template_name, context)


def report_search(request):
    template_name = "backend/report_search.html"

    if request.method == "GET":
        form = ReportSearchForm(initial={"full_text_search_type": 0})
    elif request.method == "POST":
        form = ReportSearchForm(request.POST)
        print("hello")
        if form.is_valid():
            print("valid")
            cleaned_data = form.cleaned_data
            # police_station_with_distt = cleaned_data.get('keywords', '')
            # ref_no = cleaned_data.get('ref_no', '')
            # ref_date = cleaned_data.get('ref_date', '')
            # ref_year = cleaned_data.get('ref_year', '')
            keywords = cleaned_data.get("keywords", "")
            # full_text_search_type = cleaned_data.get('full_text_search_type', '')
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
            print(f"MAP OR LIST IS {map_or_list}")
            if advanced_search_report:
                query_object = Q(entry_date__gte=min_date) & Q(entry_date__lte=max_date)
                if keywords != "":
                    query_object = query_object & Q(description__icontains=keywords)
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
                reports = Report.objects.filter(query_object).only(
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
                    context = {}
                    context["title"] = "Advanced Search Results"
                    paginator = Paginator(reports, 5)
                    page_number = request.GET.get("page")
                    page_obj = paginator.get_page(page_number)
                    context["reports"] = page_obj
                    template_name = "backend/advanced_report_search_results.html"
                    return render(request, template_name, context)
                else:
                    report_dicts = []
                    for report in reports:
                        report_dict = {}
                        report_dict["lat"] = report.location.x
                        report_dict["lon"] = report.location.y
                        report_dict["photo"] = report.photo.url
                        report_dict["icon"] = report.icon.url
                        report_dict["entry_date"] = report.entry_date
                        report_dict["name"] = report.name
                        report_dict[
                            "guardian_name_and_address"
                        ] = report.guardian_name_and_address
                        report_dict["description"] = report.description
                        report_dict["age"] = report.age
                        report_dict["height"] = report.height
                        report_dict[
                            "police_station"
                        ] = report.police_station.ps_with_distt
                        report_dict["oc"] = report.police_station.officer_in_charge
                        report_dict["tel"] = report.police_station.telephones
                        report_dicts.append(report_dict)
                    template_name = "backend/reports_map.html"
                    context = {}
                    template = "backend/reports_map_dummy.html"
                    context["mapbox_access_token"] = mapbox_access_token
                    context["reports_json"] = report_dicts
                    context["location"] = [given_location.y, given_location.x]
                    print(context["location"])
                    return render(request, template, context)
                return render(request, template_name, context)
            else:
                results = "foo"
                if len(results) != 0:
                    pass
                    # return redirect(report)
                else:
                    return redirect("backend: report_search")

                # template_name = "searches/report_search_results"

        else:
            pass
            #####
    context = {}
    context["form"] = form
    context["mapbox_access_token"] = mapbox_access_token
    context["form_title"] = "Basic and Advanced Search for Reports"
    context["title"] = "Report Search"
    return render(request, template_name, context)
