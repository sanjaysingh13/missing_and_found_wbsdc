# import io
import json
import re
# import traceback
import urllib

import cv2
import face_recognition
import numpy as np
# import requests
# from celery.result import AsyncResult
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
# from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
# from django.core.paginator import Paginator
# from django.http import HttpResponse  # , JsonResponse, request
from django.shortcuts import redirect, render

from missing_persons_match_unidentified_dead_bodies.backend.models import Report
# from django.views.decorators.cache import cache_page
# from django.views.decorators.csrf import csrf_protect
from missing_persons_match_unidentified_dead_bodies.users.models import PoliceStation

from .forms import ReportForm

local_file_pattern = re.compile(r".*media.*")
root = (
    "/Users/sanjaysingh/non_icloud/"
    + "missing_persons_match_unidentified_dead_bodies/"
    + "missing_persons_match_unidentified_dead_bodies"
)


def match_encodings(report):
    face_encoding = report.face_encoding
    face_encoding = json.loads(face_encoding)
    face_encoding = np.array(face_encoding, dtype="float64")
    print(face_encoding.dtype)
    gender = report.gender
    missing_or_found = report.missing_or_found
    height = report.height
    # entry_date = report.entry_date
    if missing_or_found == "M":
        required = "F"
    else:
        required = "M"
    print((gender, required))
    reports_under_consideration = Report.objects.filter(
        gender=gender, missing_or_found=required
    )
    print(reports_under_consideration)
    if height:
        reports_under_consideration = reports_under_consideration.filter(
            height__gte=height - 10, height__lte=height + 10
        )
    # reports_under_consideration = reports_under_consideration.filter(
    # entry_date__gte=entry_date-10,entry_date__lte=entry_date+90)
    print(reports_under_consideration)
    face_encodings = [
        np.array(json.loads(report.face_encoding), dtype="float64")
        for report in reports_under_consideration
    ]
    ids = [report.pk for report in reports_under_consideration]
    all_matches = face_recognition.compare_faces(
        face_encodings, face_encoding, tolerance=0.5
    )
    print(all_matches)
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
            missing_or_found = cleaned_data.get("missing_or_found", "")
            height = cleaned_data.get("height", "")
            description = cleaned_data.get("description", "")
            latitude = cleaned_data.get("latitude", "")
            longitude = cleaned_data.get("longitude", "")
            police_station_with_distt = cleaned_data.get(
                "police_station_with_distt", ""
            )

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
                )
                report.save()
                police_station = PoliceStation.objects.get(
                    ps_with_distt=police_station_with_distt.strip()
                )
                report.police_station = police_station
                report.save()
                url = report.photo.url
                # Load report and encode with face_recognition
                if local_file_pattern.search(url):
                    root = (
                        "/Users/sanjaysingh/non_icloud/"
                        + "missing_persons_match_unidentified_dead_bodies/"
                        + "missing_persons_match_unidentified_dead_bodies"
                    )

                    url = root + url
                    img = face_recognition.load_image_file(url)
                    face_encoding = face_recognition.face_encodings(img)[0]
                    print(face_encoding.dtype)
                else:
                    url = url.replace("ccs-django", "ccs-django-uploads")
                    req = urllib.request.urlopen(url)
                    arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
                    report = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
                    cv2.imwrite("tmp.jpg", img)
                    image = face_recognition.load_report_file("tmp.jpg")
                    face_encoding = face_recognition.face_encodings(image)[0]

                face_encoding = json.dumps(face_encoding.tolist())
                # Reverse process
                # face_encoding = json.loads(face_encoding)
                # face_encoding = np.array(face_encoding)
                report.face_encoding = face_encoding
                report.save()
                return redirect("backend:view_report", object_id=report.id)
    return render(request, template_name, {"reportsform": reportsform})


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
