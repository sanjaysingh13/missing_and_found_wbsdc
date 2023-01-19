from datetime import datetime

# from dateutil.parser import parse
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.db.models import Q
from django.http import JsonResponse

from missing_persons_match_unidentified_dead_bodies.backend.models import Report

mapbox_access_token = settings.MAP_BOX_ACCESS_TOKEN


# from django.shortcuts import redirect, render
def public_missing(request):
    min_date = request.GET.get("min_date", None)
    max_date = request.GET.get("max_date", None)
    longitude = request.GET.get("longitude", None)
    latitude = request.GET.get("latitude", None)
    # format
    date_format = "%Y-%m-%d"

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
    distance = 200 * 1000
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
    # context = {}
    # template = "backend/reports_map_dummy.html"
    # context["mapbox_access_token"] = mapbox_access_token
    # context["reports_json"] = report_dicts
    # context["location"] = [latitude, longitude]
    # response = JsonResponse(context, safe=False)
    # response["Access-Control-Allow-Origin"] = "*"
    # response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    # response["Access-Control-Max-Age"] = "1000"
    # response["Access-Control-Allow-Headers"] = "X-Requested-With, Content-Type"
    # return HttpResponseRedirect('/backend/report_search')
    # return response
    # return render(request, template, context)
    return JsonResponse(data)
