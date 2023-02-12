# import io
import hashlib
import io
import json
import random
import re
from datetime import date, timedelta
from itertools import chain

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
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Count, Q
# from django.contrib.gis.geos import Point
# from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
# from django.core.paginator import Paginator
from django.http import JsonResponse  # , , request
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.edit import DeleteView
from fuzzywuzzy import process
from rest_framework import viewsets

from missing_persons_match_unidentified_dead_bodies.backend.models import (
    AdvancedReportSearch,
    EmailRecord,
    Match,
    PublicReport,
    PublicReportMatch,
    Report,
)
from missing_persons_match_unidentified_dead_bodies.backend.serializers import (
    ReportSerializer,
)
from missing_persons_match_unidentified_dead_bodies.backend.tasks import (
    send_public_report_created_mail,
)
# from django.views.decorators.cache import cache_page
# from django.views.decorators.csrf import csrf_protect
from missing_persons_match_unidentified_dead_bodies.users.models import (
    District,
    PoliceStation,
    User,
)

from .forms import (
    BoundedBoxSearchForm,
    ConfirmPublicReportForm,
    DistrictForm,
    PublicForm,
    PublicReportForm,
    PublicReportSearchForm,
    ReportForm,
    ReportFormEdit,
    ReportSearchForm,
)
from .utils import generate_map_from_reports, get_reports_within_bbox, resize_image

# from rest_framework.renderers import JSONRenderer
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
        gender=gender, missing_or_found=required, reconciled=False
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


def match_encodings_with_public_reports(report):
    matched_images = None
    face_encoding = report.face_encoding
    face_encoding = json.loads(face_encoding)
    face_encoding = np.array(face_encoding, dtype="float64")
    gender = report.gender
    missing_or_found = report.missing_or_found
    height = report.height
    # entry_date = report.entry_date
    if missing_or_found == "F":
        reports_under_consideration = PublicReport.objects.filter(gender=gender)
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
                ids.append(report.token)
        if face_encodings != []:
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
            police_station = PoliceStation.objects.get(
                ps_with_distt=police_station_with_distt.strip()
            )
            try:
                existing_report = Report.objects.get(
                    police_station=police_station,
                    entry_date=entry_date,
                    reference=reference,
                )
                return redirect("backend:view_report", object_id=existing_report.id)
            except Report.DoesNotExist:
                pass
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
                report.reconciled = False
                report.save()
                return redirect("backend:view_report", object_id=report.id)
    return render(
        request,
        template_name,
        {
            "reportsform": reportsform,
            "mapbox_access_token": mapbox_access_token,
            "heading": "Upload photo of missing/found person",
        },
    )


def upload_public_report(request):
    template_name = "backend/photo_upload_form.html"
    if request.method == "GET":
        reportsform = PublicReportForm(request.GET or None)
    elif request.method == "POST":
        reportsform = PublicReportForm(request.POST, request.FILES)
        if reportsform.is_valid():
            files = request.FILES.getlist("photo")
            cleaned_data = reportsform.cleaned_data
            name = cleaned_data.get("name", "")
            gender = cleaned_data.get("gender", "")
            age = cleaned_data.get("age", "")
            guardian_name_and_address = cleaned_data.get(
                "guardian_name_and_address", ""
            )
            missing_or_found = "M"
            height = cleaned_data.get("height", "")
            description = cleaned_data.get("description", "")
            police_station_with_distt = cleaned_data.get(
                "police_station_with_distt", ""
            )
            location = cleaned_data.get("location", "")
            telephone_of_missing = cleaned_data.get("telephone_of_missing", "")
            telephone_of_reporter = cleaned_data.get("telephone_of_reporter", "")
            email_of_reporter = cleaned_data.get("email_of_reporter", "")
            entry_date = cleaned_data.get("entry_date", "")
            otp = cleaned_data.get("otp", "")
            token = str(random.randint(10000000, 99999999))
            random_string = "s86hjaulop9&^2@"
            string = random_string + telephone_of_reporter
            string_hash = hashlib.sha256(string.encode()).hexdigest()
            num = int(string_hash, 16)
            num_str = str(num)[:6].zfill(6)
            print(f"OTP is {otp} Num String is {num_str}")
            if otp == num_str:
                # Encoding face
                for f in files:
                    resized_image, icon = resize_image(f, 600, 64)
                    report = PublicReport(
                        photo=resized_image,
                        icon=icon,
                        telephone_of_missing=telephone_of_missing,
                        telephone_of_reporter=telephone_of_reporter,
                        email_of_reporter=email_of_reporter,
                        token=token,
                        entry_date=entry_date,
                        name=name,
                        gender=gender,
                        missing_or_found=missing_or_found,
                        height=height,
                        description=description,
                        age=age,
                        location=location,
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
                    report.reconciled = False
                    report.save()
                    send_public_report_created_mail.apply_async(
                        args=[report.pk], countdown=5
                    )
                    return redirect(
                        "backend:view_public_report", object_id=report.token
                    )
                else:
                    messages.info(request, "Please enter the correct OTP")
                    return render(
                        request,
                        template_name,
                        {
                            "reportsform": reportsform,
                            "mapbox_access_token": mapbox_access_token,
                        },
                    )

    return render(
        request,
        template_name,
        {
            "reportsform": reportsform,
            "mapbox_access_token": mapbox_access_token,
            "heading": "Upload photo of missing person",
        },
    )


@login_required
@permission_required("users.add_user", raise_exception=True)
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
        matched_public_reports = match_encodings_with_public_reports(report)
        if matched_public_reports:
            public_reports = PublicReport.objects.filter(
                token__in=matched_public_reports
            ).only(
                "pk",
                "token",
                "photo",
                "description",
                "entry_date",
                "name",
                "police_station",
            )
            for report_missing in public_reports:
                if not PublicReportMatch.objects.filter(
                    report_missing=report_missing, report_found=report
                ).exists():
                    match = PublicReportMatch(
                        report_missing=report_missing, report_found=report
                    )
                    match.save()
            reports = list(chain(public_reports, reports))
    print(f"<<<<<<<<{reports}")

    context["report"] = report
    paginator = Paginator(reports, 2)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context["matches"] = page_obj
    template_name = "backend/report_detail.html"
    return render(request, template_name, context)


def view_public_report(request, object_id):
    if request.method == "GET":
        confirmform = ConfirmPublicReportForm(request.GET or None)
        report = PublicReport.objects.get(token=object_id)
        context = {}
        reports = []
        if report.face_encoding:
            matched_reports = match_encodings(report)
            if matched_reports:
                reports = Report.objects.filter(pk__in=matched_reports).only(
                    "pk", "photo", "description", "entry_date", "name", "police_station"
                )
                for report_found in reports:
                    if not PublicReportMatch.objects.filter(
                        report_missing=report, report_found=report_found
                    ).exists():
                        match = PublicReportMatch(
                            report_missing=report, report_found=report_found
                        )
                        match.save()
        context["report"] = report
        paginator = Paginator(reports, 2)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        context["matches"] = page_obj
        context["form"] = confirmform
        template_name = "backend/public_report_detail.html"
        return render(request, template_name, context)
    elif request.method == "POST":
        public_report = PublicReport.objects.get(token=object_id)
        confirmform = ConfirmPublicReportForm(request.POST)
        if confirmform.is_valid():
            cleaned_data = confirmform.cleaned_data
            reference = cleaned_data.get("reference", "")
            entry_date = cleaned_data.get("entry_date", "")
            new_report = Report(
                photo=public_report.photo,
                reference=reference,
                entry_date=entry_date,
                name=public_report.name,
                gender=public_report.gender,
                missing_or_found="M",
                height=public_report.height,
                description=public_report.description,
                location=public_report.location,
                age=public_report.age,
                guardian_name_and_address=public_report.guardian_name_and_address,
                police_station=public_report.police_station,
                face_encoding=public_report.face_encoding,
            )
            new_report.save()
            report_created_message = f"""A missing report has been filed at
            {new_report.police_station.ps_with_distt}
            vide Reference No {reference}
            dated {entry_date.strftime('%d,%b,%Y')}"""
            send_mail(
                "Police Station reference for missing person reported by you on WB Khoya Paya",
                report_created_message,
                None,
                [public_report.email_of_reporter],
                fail_silently=False,
            )

            return redirect("backend:view_report", object_id=new_report.id)


def edit_report(request, pk):
    report = Report.objects.get(id=pk)
    report_params = {
        k: report.__dict__[k]
        for k in set(report.__dict__.keys())
        & {
            "pk",
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
            "reconciled",
        }
    }
    police_station = report.police_station.ps_with_distt
    report_params["police_station_with_distt"] = police_station
    if request.method == "POST":
        reportsform = ReportFormEdit(request.POST, request.FILES)
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
            reconciled = cleaned_data.get("reconciled", "")
            police_station = PoliceStation.objects.get(
                ps_with_distt=police_station_with_distt.strip()
            )
            try:
                existing_report = Report.objects.get(
                    police_station=police_station,
                    entry_date=entry_date,
                    reference=reference,
                )
                message = (
                    "A report with this reference already"
                    + "exists at https://www.wbkhoyapaya.com/backend/"
                    + f"view_report/{existing_report.pk}/ "
                )
                messages.info(request, message)
                return render(
                    request,
                    "backend/photo_upload_form.html",
                    {"reportsform": reportsform},
                )
            except Report.DoesNotExist:
                pass
            if files:
                for f in files:
                    resized_image, icon = resize_image(f, 600, 64)
                    report.photo = resized_image
                    report.icon = icon
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

            report.police_station = police_station

            report.year = str(entry_date.year)[-2:]
            if location:
                report.location = location
            else:
                report.location = Point(longitude, latitude)
            report.reference = reference
            report.entry_date = entry_date
            report.name = name
            report.gender = gender
            report.age = age
            report.guardian_name_and_address = guardian_name_and_address
            report.missing_or_found = missing_or_found
            report.height = height
            report.description = description
            if reconciled:
                report.reconciled = True
            report.save()
            return redirect("backend:view_report", object_id=report.id)
    else:
        reportsform = ReportFormEdit(initial=report_params)
    return render(
        request, "backend/photo_upload_form.html", {"reportsform": reportsform}
    )


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
                if map_or_list == "L":
                    advanced_report_search = AdvancedReportSearch.objects.create(
                        keywords=keywords,
                        full_text_search_type=full_text_search_type,
                        districts=districts,
                        ps_list=ps_list,
                        min_date=min_date,
                        max_date=max_date,
                        missing_or_found=missing_or_found,
                        gender=gender,
                        latitude=latitude,
                        longitude=longitude,
                        distance=distance,
                        location=location,
                    )
                    return redirect(advanced_report_search)
                else:
                    if not min_date:
                        min_date = date.today() - timedelta(days=30)
                    if not max_date:
                        max_date = date.today()
                    query_object = (
                        Q(entry_date__gte=min_date)
                        & Q(entry_date__lte=max_date)
                        & Q(reconciled=False)
                    )

                    if districts != "Null":
                        query_object = query_object & Q(
                            police_station__district__in=[int(districts)]
                        )
                        districts = districts
                    if ps_list != "":
                        police_stations = ps_list.split(", ")
                        police_stations = [
                            int(ps.strip()) for ps in police_stations if ps
                        ]
                        police_stations = list(filter(None, police_stations))
                        query_object = query_object & Q(
                            police_station__pk__in=police_stations
                        )
                    if missing_or_found != "All":
                        query_object = query_object & Q(
                            missing_or_found=missing_or_found
                        )
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
                            reports = reports.annotate(search=vector).filter(
                                search=query
                            )
                        elif full_text_search_type == 1:
                            choices = [
                                r.description + f" $primary_key={r.pk}" for r in reports
                            ]
                            results = process.extract(keywords, choices, limit=10)
                            results = [
                                result for (result, score) in results if score > 50
                            ]
                            print(results)
                            results = [
                                int(pk_pattern.search(string).group(1))
                                for string in results
                            ]
                            print(results)
                            reports = reports.filter(pk__in=results)
                            # testing serialisation
                            # serializer = ReportSerializer(reports, many=True)
                            # print(JSONRenderer().render(serializer.data))

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
                    # if map_or_list == "L":
                    #     reports = reports.values()
                    #     report_list = []
                    #     for report in reports:
                    #         id_ = report["id"]
                    #         report_ = {} # Solving N+1
                    #         rep = Report.objects.get(pk=id_)
                    #         # N+1
                    #         report_["id"] = id_
                    #         report_["name"] = rep.name
                    #         report_["missing_or_found"] = rep.missing_or_found
                    #         report_["guardian_name_and_address"] = rep.guardian_name_and_address
                    #         report_["age"] = rep.age
                    #         report_["height"] = rep.height
                    #         report_["entry_date"] = rep.entry_date
                    #         report_["description"] = rep.description
                    #         report_["matched"] = (
                    #             Match.objects.filter(report_found=rep).exists()
                    #             or Match.objects.filter(report_missing=rep).exists()
                    #         )
                    #         report_["photo"] = rep.photo.url
                    #         report_["ps"] = rep.police_station.ps_with_distt
                    #         report_["oc"] = rep.police_station.officer_in_charge
                    #         report_["tel"] = rep.police_station.telephones
                    #         report_list.append(report_)
                    #     reports = report_list
                    #     context = {}
                    #     context["title"] = "Advanced Search Results"
                    #     paginator = Paginator(reports, 5)
                    #     page_number = request.GET.get("page")
                    #     page_obj = paginator.get_page(page_number)
                    #     context["reports"] = page_obj
                    #     template_name = "backend/advanced_report_search_results.html"
                    #     return render(request, template_name, context)
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


@permission_required("users.view_user", raise_exception=True)
@login_required
def report_search_results(request, pk):
    advanced_report_search = AdvancedReportSearch.objects.get(pk=pk)
    min_date = advanced_report_search.min_date
    max_date = advanced_report_search.max_date
    districts = advanced_report_search.districts
    ps_list = advanced_report_search.ps_list
    missing_or_found = advanced_report_search.missing_or_found
    gender = advanced_report_search.gender
    location = advanced_report_search.location
    latitude = advanced_report_search.latitude
    longitude = advanced_report_search.longitude
    keywords = advanced_report_search.keywords
    distance = advanced_report_search.distance
    full_text_search_type = advanced_report_search.full_text_search_type

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
        # testing serialisation
        # serializer = ReportSerializer(reports, many=True)
        # print(JSONRenderer().render(serializer.data))

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
    reports = reports.values()
    report_list = []
    for report in reports:
        id_ = report["id"]
        report_ = {}  # Solving N+1
        rep = Report.objects.get(pk=id_)
        # N+1
        report_["id"] = id_
        report_["name"] = rep.name
        report_["missing_or_found"] = rep.missing_or_found
        report_["guardian_name_and_address"] = rep.guardian_name_and_address
        report_["age"] = rep.age
        report_["height"] = rep.height
        report_["entry_date"] = rep.entry_date
        report_["description"] = rep.description
        report_["matched"] = (
            Match.objects.filter(report_found=rep).exists()
            or Match.objects.filter(report_missing=rep).exists()
        )
        report_["photo"] = rep.photo.url
        report_["ps"] = rep.police_station.ps_with_distt
        report_["oc"] = rep.police_station.officer_in_charge
        report_["tel"] = rep.police_station.telephones
        report_list.append(report_)
    reports = report_list
    context = {}
    context["title"] = "Advanced Search Results"
    paginator = Paginator(reports, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context["reports"] = page_obj
    messages.info(request, f"Your search has {len(reports)} results.")
    template_name = "backend/advanced_report_search_results.html"
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
    context["title"] = "Missing Persons Near You"
    return render(request, template_name, context)


def district(request):
    template_name = "backend/district.html"
    if request.method == "GET":
        form = DistrictForm()
    elif request.method == "POST":
        form = DistrictForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            district_id = cleaned_data.get("districts", "")
            district = District.objects.get(pk=district_id)
            sp_or_cp_users = User.objects.filter(district=district, is_sp_or_cp=True)
            distt_admins = User.objects.filter(
                district=district, category="DISTRICT_ADMIN"
            )
            oc_users = User.objects.filter(
                district=district, police_station__isnull=False, category="PS_ADMIN"
            ).order_by("police_station__name")
            empty_police_stations = district.policestation_set.exclude(user__is_oc=True)
            print(district_id)
            context = {}
            context["form"] = form
            context["sp_or_cp_users"] = sp_or_cp_users
            context["distt_admins"] = distt_admins
            context["oc_users"] = oc_users
            context["empty_police_stations"] = empty_police_stations
            return render(request, template_name, context)
    context = {}
    context["form"] = form
    context["form_title"] = "Districts At A Glance"
    context["title"] = "Districts At A Glance"
    return render(request, template_name, context)


@login_required
@permission_required("users.add_user", raise_exception=True)
def districts_at_glance_reports(request):
    template_name = "backend/districts_at_glance_reports.html"
    if request.method == "GET":
        now = timezone.now()
        yesterday = now - timezone.timedelta(hours=24)
        district_reports = (
            District.objects.annotate(
                missing_count=Count(
                    "policestation__report",
                    filter=Q(policestation__report__missing_or_found="M"),
                ),
                found_count=Count(
                    "policestation__report",
                    filter=Q(policestation__report__missing_or_found="F"),
                ),
                missing_last_24_hours=Count(
                    "policestation__report",
                    filter=Q(
                        policestation__report__missing_or_found="M",
                        policestation__report__created__gte=yesterday,
                    ),
                ),
                found_last_24_hours=Count(
                    "policestation__report",
                    filter=Q(
                        policestation__report__missing_or_found="F",
                        policestation__report__created__gte=yesterday,
                    ),
                ),
            )
            .values(
                "name",
                "missing_count",
                "found_count",
                "missing_last_24_hours",
                "found_last_24_hours",
            )
            .order_by("name")
        )

        context = {}
        context["district_reports"] = district_reports
        context["form_title"] = "Districts At A Glance (Reports)"
        context["title"] = "Districts At A Glance (Reports)"
    return render(request, template_name, context)


@login_required
@permission_required("users.add_user", raise_exception=True)
def users_at_glance(request):
    template_name = "backend/users_at_glance.html"
    if request.method == "GET":

        users_with_reports = (
            Report.objects.select_related("uploaded_by")
            .values(
                "uploaded_by__username",
                "uploaded_by__name",
                "uploaded_by__rank",
                "uploaded_by__police_station__district__name",
            )
            .annotate(report_count=Count("id"))
            .order_by("-report_count")
        )
        context = {}
        context["users"] = users_with_reports
        context["form_title"] = "Users At A Glance"
        context["title"] = "Users At A Glance"
    return render(request, template_name, context)


@login_required
@permission_required("users.add_user", raise_exception=True)
def districts_at_glance_public_reports(request):
    template_name = "backend/districts_at_glance_reports.html"
    if request.method == "GET":
        now = timezone.now()
        yesterday = now - timezone.timedelta(hours=24)
        district_reports = (
            District.objects.annotate(
                missing_count=Count(
                    "policestation__publicreport",
                    filter=Q(policestation__publicreport__missing_or_found="M"),
                ),
                found_count=Count(
                    "policestation__publicreport",
                    filter=Q(policestation__publicreport__missing_or_found="F"),
                ),
                missing_last_24_hours=Count(
                    "policestation__publicreport",
                    filter=Q(
                        policestation__publicreport__missing_or_found="M",
                        policestation__publicreport__created__gte=yesterday,
                    ),
                ),
                found_last_24_hours=Count(
                    "policestation__publicreport",
                    filter=Q(
                        policestation__publicreport__missing_or_found="F",
                        policestation__publicreport__created__gte=yesterday,
                    ),
                ),
            )
            .values(
                "name",
                "missing_count",
                "found_count",
                "missing_last_24_hours",
                "found_last_24_hours",
            )
            .order_by("name")
        )

        context = {}
        context["district_reports"] = district_reports
        context["form_title"] = "Districts At A Glance (Public Reports)"
        context["title"] = "Districts At A Glance (Public Reports)"
    return render(request, template_name, context)


@login_required
@permission_required("users.add_user", raise_exception=True)
def public_report_search(request):
    template_name = "backend/public_report_search.html"
    if request.method == "GET":
        form = PublicReportSearchForm()
    elif request.method == "POST":
        print("hi")
        form = PublicReportSearchForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            print(cleaned_data)
            token = cleaned_data.get("token_given_via_mail", "")
            email_of_reporter = cleaned_data.get("email_of_public", "")
            telephone_of_reporter = cleaned_data.get("telephone_of_public", "")
            # Start with a Q object that matches all Report objects
            # Use the Q object to filter the Report objects
            public_reports = PublicReport.objects.filter(
                token=token,
                email_of_reporter=email_of_reporter,
                telephone_of_reporter=telephone_of_reporter,
            )
            if not public_reports.exists():
                context = {}
                context["form"] = form
                context["form_title"] = "Search for Public Report"
                context["title"] = "Search for Public Report"
                messages.info(request, "No report found")
                return render(request, template_name, context)
            else:
                return redirect("backend:view_public_report", public_reports[0].token)
    context = {}
    context["form"] = form
    context["form_title"] = "Search for Public Report"
    context["title"] = "Search for Public Report"
    return render(request, template_name, context)


@csrf_exempt
def handle_sendgrid_post(request):
    if request.method == "POST":
        # Get the incoming request data
        request_data = json.loads(request.body)

        # Store the data in the database
        EmailRecord.objects.create(email=request_data["email"], data=request_data)

        # Return a success response
        return JsonResponse({"status": "success"})
    else:
        # Return an error response for other request methods
        return JsonResponse({"status": "error"})
