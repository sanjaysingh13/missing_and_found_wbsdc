import hashlib
from datetime import datetime

# from dateutil.parser import parse
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.gis.geos import GEOSGeometry
# from django.core.mail import send_mail
from django.db.models import Q
from django.http import HttpResponse, JsonResponse

from missing_persons_match_unidentified_dead_bodies.backend.models import Match, Report
from missing_persons_match_unidentified_dead_bodies.backend.tasks import send_sms

mapbox_access_token = settings.MAP_BOX_ACCESS_TOKEN
generate_token = settings.TEMPLATEID_GENERATE_TOKEN

# format
date_format = "%Y-%m-%d"


def send_otp(request):
    telephone_of_reporter = request.GET.get("telephone_of_reporter", None)
    # email_of_reporter = request.GET.get("email_of_reporter", None)
    random_string = "s86hjaulop9&^2@"
    string = random_string + telephone_of_reporter
    string_hash = hashlib.sha256(string.encode()).hexdigest()
    num = int(string_hash, 16)
    num_str = str(num)[:6].zfill(6)
    # otp_message = f"Your OTP is {num_str}"
    # send_mail(
    #     "OTP for registering missing person report on WB Khoya Paya",
    #     otp_message,
    #     None,
    #     [email_of_reporter],
    #     fail_silently=False,
    # )
    otp_message = f"Your token for missing person Sanjay Singh is {num_str}. GoWB"
    send_sms(generate_token, otp_message, telephone_of_reporter)
    return HttpResponse(status=200)


def get_missing_persons(request):
    min_date = request.GET.get("min_date", None)
    max_date = request.GET.get("max_date", None)
    min_date = datetime.strptime(min_date, date_format).date()
    max_date = datetime.strptime(max_date, date_format).date()
    gender = request.GET.get("gender", None)
    latitude = request.GET.get("lat", None)
    longitude = request.GET.get("lng", None)
    query_object = Q(entry_date__gte=min_date) & Q(entry_date__lte=max_date)
    query_object = query_object & Q(gender=gender)
    query_object = query_object & Q(missing_or_found="F")

    # latitude = data["lat"]
    # longitude = data['lon']
    given_location = GEOSGeometry(f"POINT({longitude} {latitude})", srid=4326)
    distance = 4 * 1000
    query_object = query_object & Q(location__dwithin=(given_location, distance))
    report_dicts = []
    reports = Report.objects.filter(query_object)
    for report in reports:
        report_dict = {}
        report_dict["lat"] = report.location.x
        report_dict["lon"] = report.location.y
        report_dict["photo"] = report.photo.url
        report_dict["icon"] = report.icon.url
        report_dict["entry_date"] = report.entry_date
        report_dict["name"] = report.name
        report_dict["guardian_name_and_address"] = report.guardian_name_and_address
        report_dict["description"] = report.description
        report_dict["age"] = report.age
        report_dict["height"] = report.height
        report_dict["police_station"] = report.police_station.ps_with_distt
        report_dict["oc"] = report.police_station.officer_in_charge
        report_dict["tel"] = report.police_station.telephones
        report_dicts.append(report_dict)
    data = {
        "reports_json": report_dicts,
    }
    return JsonResponse(data)


def public_missing(request):
    min_date = request.GET.get("min_date", None)
    max_date = request.GET.get("max_date", None)
    longitude = request.GET.get("longitude", None)
    latitude = request.GET.get("latitude", None)

    # convert from string format to datetime format
    min_date = datetime.strptime(min_date, date_format).date()
    max_date = datetime.strptime(max_date, date_format).date()
    print(
        f"""
        Mindate : {min_date}\n
        Maxdate : {max_date}\n
        longitude : {longitude}\n
        latitude : {latitude}
        """
    )

    query_object = Q(entry_date__gte=min_date) & Q(entry_date__lte=max_date)
    given_location = GEOSGeometry(f"POINT({longitude} {latitude})", srid=4326)
    # distance = 20 * 1000
    distance = 50 * 1000
    query_object = query_object & Q(location__dwithin=(given_location, distance))
    report_dicts = []
    reports = Report.objects.filter(query_object)
    for report in reports:
        report_dict = {}
        report_dict["lat"] = report.location.x
        report_dict["lon"] = report.location.y
        report_dict["photo"] = report.photo.url
        report_dict["icon"] = report.icon.url
        report_dict["entry_date"] = report.entry_date
        report_dict["name"] = report.name
        report_dict["guardian_name_and_address"] = report.guardian_name_and_address
        report_dict["description"] = report.description
        report_dict["age"] = report.age
        report_dict["height"] = report.height
        report_dict["police_station"] = report.police_station.ps_with_distt
        report_dict["oc"] = report.police_station.officer_in_charge
        report_dict["tel"] = report.police_station.telephones
        report_dicts.append(report_dict)
    print(report_dicts)

    data = {
        "reports_json": report_dicts,
        "given_location": [longitude, latitude],
        "mapbox_access_token": mapbox_access_token,
    }
    return JsonResponse(data)


@login_required
@permission_required("users.add_user", raise_exception=True)
def merge_matches(request):
    list_of_suggested_matches = request.GET.get("list_of_suggested_matches", None)
    list_of_suggested_matches = list_of_suggested_matches.split(",")
    list_of_suggested_matches = [
        int(suggested_match) for suggested_match in list_of_suggested_matches
    ]
    merger_action_to_be_taken = request.GET.get("merger_action_to_be_taken", None)
    accepted_matches = request.GET.get("accepted_matches", None)
    if accepted_matches != "":
        accepted_matches = accepted_matches.split(",")
        accepted_matches = [int(accepted_match) for accepted_match in accepted_matches]
    else:
        accepted_matches = []
    not_matched = [
        match for match in list_of_suggested_matches if match not in accepted_matches
    ]

    report_id = int(request.GET.get("report_id", None))
    report_m_or_f = request.GET.get("report_m_or_f", None)
    if merger_action_to_be_taken == "1":
        if report_m_or_f == "M":
            matches = Match.objects.filter(
                report_missing_id=report_id, report_found_id__in=accepted_matches
            )
            not_matched = Match.objects.filter(
                report_missing_id=report_id, report_found_id__in=not_matched
            )
        else:
            matches = Match.objects.filter(
                report_found_id=report_id, report_missing_id__in=accepted_matches
            )
            not_matched = Match.objects.filter(
                report_found_id=report_id, report_missing_id__in=not_matched
            )
        for match in matches:
            match.match_is_correct = True
            match.save()
            report_missing = match.report_missing
            report_missing.reconciled = True
            report_missing.save()
            report_found = match.report_found
            report_found.reconciled = True
            report_found.save()
        for match in not_matched:
            match.match_is_correct = False
            match.save()

    elif merger_action_to_be_taken == "2":
        if report_m_or_f == "M":
            not_matched = Match.objects.filter(
                report_missing_id=report_id,
                report_found_id__in=list_of_suggested_matches,
            )
        else:
            not_matched = Match.objects.filter(
                report_found_id=report_id,
                report_missing_id__in=list_of_suggested_matches,
            )
        for match in not_matched:
            match.match_is_correct = False
            match.save()
    data = {"foo": "bar"}
    return JsonResponse(data)
