import csv
import pickle
from datetime import datetime
from io import BytesIO

import cv2
import numpy as np
import regex as re
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
    filename = "./filtered_data.csv"
    with open(filename) as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)  # Skip the first row (header row)
        for row in csvreader:
            name = row[1]
            if row[3] != "":
                age = int(row[3])
            else:
                age = 0
            if row[4] != "":
                height = int(row[4])
            else:
                height = 0
            if row[5] != "":
                latitude = float(row[5])
            else:
                latitude = None
            if row[6] != "":
                longitude = float(row[6])
            else:
                longitude = None
            if row[7] != "":
                reference = int(row[7])
            else:
                reference = None
            if row[8] != "":
                entry_date = datetime.strptime(row[8], "%Y-%m-%d").date()
            else:
                entry_date = None
            if row[13] != "":
                description = row[13]
            else:
                description = ""
            missing_or_found = row[10]
            gender = row[9]
            if missing_or_found == "Unknown" or gender == "Unknown":
                continue
            if row[14] != "":
                face_encoding = row[14]
            else:
                face_encoding = None
            print(row[0])
            photo_file = f"./resized_photos/{row[0]}"
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
                guardian_name_and_address=description,
                face_encoding=face_encoding,
            )
            ps = PoliceStation.objects.get(pk=int(row[11]))
            report.police_station = ps
            with open(photo_file, "rb") as f:
                file = ContentFile(f.read())
                report.photo.save(row[0], file, save=True)
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
    lines = [LineString(path[i: i + 2]) for i in range(len(path) - 1)]
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
