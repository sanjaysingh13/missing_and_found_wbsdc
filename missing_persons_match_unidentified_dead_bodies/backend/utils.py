import pickle
from io import BytesIO

import cv2
import numpy as np
import pandas as pd
import regex as re
from anymail.backends.sendgrid import EmailBackend
from django.contrib.gis.geos import LineString, MultiLineString, Point, Polygon
from django.contrib.gis.measure import D
from django.contrib.gis.utils import LayerMapping
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile

from missing_persons_match_unidentified_dead_bodies.backend.models import (
    MitRailLines,
    MitRoadLines,
    MitWaterLines,
    Report,
)
from missing_persons_match_unidentified_dead_bodies.users.models import PoliceStation


# Returns resized for upload and for icon
def resize_image(file, size_image, size_icon):
    print(size_image)
    # Open the uploaded file as an image
    image = cv2.imdecode(np.fromstring(file.read(), np.uint8), cv2.IMREAD_UNCHANGED)

    # Get the aspect ratio of the image
    aspect_ratio = float(image.shape[1]) / image.shape[0]

    # Compute the new dimensions of the image
    new_height = int(size_image)
    new_width = int(new_height * aspect_ratio)

    icon_height = int(size_icon)
    icon_width = int(icon_height * aspect_ratio)

    # Resize the image
    resized_image = cv2.resize(image, (new_width, new_height))
    image_icon = cv2.resize(resized_image, (icon_width, icon_height))

    # Encode the resized image
    ret, image_buffer = cv2.imencode(".jpg", resized_image)
    image_buffer = BytesIO(image_buffer)
    resized_image = InMemoryUploadedFile(
        image_buffer,
        None,
        file.name,
        "image/jpeg",
        image_buffer.getbuffer().nbytes,
        None,
    )
    # Icon
    ret, icon_buffer = cv2.imencode(".jpg", image_icon)
    icon_buffer = BytesIO(icon_buffer)
    image_icon = InMemoryUploadedFile(
        icon_buffer,
        None,
        "icon_" + file.name,
        "image/jpeg",
        icon_buffer.getbuffer().nbytes,
        None,
    )
    return (resized_image, image_icon)


def initial_migration():
    filename = "./filtered_data.pkl"
    r = open(filename, "rb")
    df = pickle.load(r)
    r.close()
    for i in range(len(df)):
        if "Basirhat Police District" not in df.iloc[i, 8]:
            try:
                report = Report.objects.get(
                    name=df.iloc[i, 1], reference=int(df.iloc[i, 12])
                )
            except Report.DoesNotExist:
                name = df.iloc[i, 1]
                if pd.notna(df.iloc[i, 10]):
                    age = int(df.iloc[i, 10])
                else:
                    age = 0
                if pd.notna(df.iloc[i, 11]):
                    height = int(df.iloc[i, 11])
                else:
                    height = 0
                if pd.notna(df.iloc[i, 6]):
                    latitude = float(df.iloc[i, 6])
                else:
                    latitude = None
                if pd.notna(df.iloc[i, 7]):
                    longitude = float(df.iloc[i, 7])
                else:
                    longitude = None
                if pd.notna(df.iloc[i, 12]):
                    reference = int(df.iloc[i, 12])
                else:
                    reference = None
                if pd.notna(df.iloc[i, 13]):
                    entry_date = df.iloc[i, 13]
                else:
                    entry_date = None
                if pd.notna(df.iloc[i, 5]):
                    description = df.iloc[i, 5]
                else:
                    description = None
                if pd.notna(df.iloc[i, 9]):
                    particulars = df.iloc[i, 9]
                else:
                    particulars = None
                missing_or_found = df.iloc[i, 4]
                if missing_or_found == "Unknown":
                    continue
                gender = df.iloc[i, 3]
                if gender == "Unknown":
                    gender = None
                if pd.notna(df.iloc[i, 14]):
                    face_encoding = df.iloc[i, 14]
                else:
                    face_encoding = None
                photo_file = f"./resized_photos/{df.iloc[i, 0]}"
                # photo_file = photo_file.replace(" ", "_")

                report = Report(
                    name=name,
                    age=age,
                    height=height,
                    latitude=latitude,
                    longitude=longitude,
                    entry_date=entry_date,
                    reference=reference,
                    missing_or_found=missing_or_found,
                    gender=gender,
                    guardian_name_and_address=particulars,
                    description=description,
                    face_encoding=face_encoding,
                    reconciled=False,
                )
                ps = PoliceStation.objects.get(ps_with_distt=df.iloc[i, 8])
                report.police_station = ps
                with open(photo_file, "rb") as f:
                    file = ContentFile(f.read())
                    report.photo.save(df.iloc[i, 0], file, save=True)
                    if longitude:
                        report.location = Point(longitude, latitude)
                    report.save()


def tokenize(text):
    stopwords = {
        word.strip()
        for word in """no,off,her,with,myself,it's,all,m,those,ain,be,mustn,theirs,against,
            being,on,wouldn't,that,wasn,more,mightn't,it,himself,only,couldn,isn,down,
            or,then,they,we,until,d,didn,wasn't,out,doesn't,than,by,don,won't,in,during,
            as,do,so,has,she's,further,through,when,themselves,shan,don't,ma,y,there,
            can,you'd,weren,its,isn't,having,most,i,itself,aren't,doing,now,you've,our,
            needn't,ve,me,wouldn,below,such,if,them,for,were,why,his,weren't,did,him,
            herself,own,re,where,my,shouldn,o,ll,over,an,above,haven,she,does,at,nor,
            too,you'll,because,each,am,the,hadn,didn't,just,should've,what,these,but,
            not,hers,which,have,a,again,couldn't,under,up,hadn't,hasn't,before,that'll,
            is,your,any,between,aren,into,needn,ours,shan't,will,he,how,few,shouldn't,
            you're,been,mightn,once,doesn,t,are,here,was,same,mustn't,after,s,
            yourselves,of,other,their,whom,had,from,some,yours,while,won,to,you,who,
            yourself,very,should,ourselves,both,haven't,this,about,and,hasn,www,
            mandal,fox,rs,manupatra,com""".split(
            ","
        )
    }

    def remove_stop(tokens):
        return [t.lower() for t in tokens if t.lower() not in stopwords]

    def tokenize(text):
        return re.findall(r"[\w-]*\p{L}[\w-]*", text)

    return remove_stop(tokenize(text))


mit_rail_lines_mapping = {
    "f_code": "f_code",
    "exs": "exs",
    "fco": "fco",
    "loc": "loc",
    "soc": "soc",
    "geom": "MULTILINESTRING",
}
mit_water_lines_mapping = {
    "f_code": "f_code",
    "hyc": "hyc",
    "lit": "lit",
    "nam": "nam",
    "soc": "soc",
    "geom": "MULTILINESTRING",
}
mit_road_lines_mapping = {
    "f_code": "f_code",
    "acc": "acc",
    "exs": "exs",
    "rst": "rst",
    "med": "med",
    "rtt": "rtt",
    "rsu": "rsu",
    "loc": "loc",
    "soc": "soc",
    "geom": "MULTILINESTRING",
}
mit_rail_lines_shp = "rail/raill_ind.shp"
mit_water_lines_shp = "river/riverl_ind.shp"
mit_road_lines_shp = "road/roadl_ind.shp"


def create_mit_layers(verbose=True):
    # Add MitRailLines
    lm = LayerMapping(
        MitRailLines, mit_rail_lines_shp, mit_rail_lines_mapping, encoding="utf-8"
    )
    lm.save(strict=True, verbose=verbose)
    # Add MitWaterLines
    lm = LayerMapping(
        MitWaterLines, mit_water_lines_shp, mit_water_lines_mapping, encoding="utf-8"
    )

    lm.save(strict=True, verbose=verbose)
    # Add Ganga from Nabadwip to Sagar
    # Load list of (lon,lat) tuples describing path
    r = open("ganga.pkl", "rb")
    path = pickle.load(r)
    r.close()
    lines = [LineString(path[i:i + 2]) for i in range(len(path) - 1)]
    multiline = MultiLineString(lines, srid=4326)
    new_waterline = MitWaterLines(
        f_code="BH140",
        hyc=8,
        lit=0,
        nam="Ganga from Nabadwip",
        soc="IND",
        geom=multiline,
    )
    new_waterline.save()
    # Add MitRoadLines
    lm = LayerMapping(
        MitRoadLines, mit_road_lines_shp, mit_road_lines_mapping, encoding="utf-8"
    )
    lm.save(strict=True, verbose=verbose)


def get_reports_within_bbox(xmin, ymin, xmax, ymax, layer="waterlines"):
    reports = Report.objects.none()
    bbox = Polygon.from_bbox((xmin, ymin, xmax, ymax))
    if layer == "waterlines":
        lines = MitWaterLines.objects.filter(geom__intersects=bbox)
        for line in lines:
            new_reports = Report.objects.filter(
                location__distance_lte=(line.geom, D(km=2))
            )
            reports = reports | new_reports
    elif layer == "raillines":
        lines = MitRailLines.objects.filter(geom__intersects=bbox)
        for line in lines:
            new_reports = Report.objects.filter(
                location__distance_lte=(line.geom, D(km=1))
            )
            reports = reports | new_reports
    elif layer == "roadlines":
        lines = MitRoadLines.objects.filter(geom__intersects=bbox)
        for line in lines:
            new_reports = Report.objects.filter(
                location__distance_lte=(line.geom, D(km=1))
            )
            reports = reports | new_reports

    reports = reports.distinct()
    reports = reports.filter(reconciled=False)
    return reports


def generate_map_from_reports(reports):
    report_dicts = []
    for report in reports:
        if not report.location:
            continue
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
    return report_dicts


class BCCEmailBackend(EmailBackend):
    def send_messages(self, email_messages):
        for message in email_messages:
            message.bcc = ["support@wbkhoyapaya.com"]
            message.from_email = "support@wbmissingfound.com"
            super().send_messages([message])
