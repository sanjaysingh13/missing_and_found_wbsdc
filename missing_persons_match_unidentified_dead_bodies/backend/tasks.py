import sys
from datetime import date
from io import BytesIO

import boto3
import requests
from dateutil import tz
from dateutil.parser import parse
from django.conf import settings
from django.contrib.postgres.search import SearchVector
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.mail import send_mail
from django.db.models import Count
from django.utils import timezone
from PIL import Image

from config.celery_app import app
from missing_persons_match_unidentified_dead_bodies.backend.models import (
    Match,
    Message,
    PublicReport,
    PublicReportMatch,
    Report,
)
from missing_persons_match_unidentified_dead_bodies.users.models import User

passkey = settings.PASSKEY
alert_oc_public_complaint = settings.TEMPLATEID_ALERT_OC_REGISTRATION_PUBLIC_COMPLAINT
generate_token = settings.TEMPLATEID_GENERATE_TOKEN
template_match = settings.TEMPLATEID_MATCH
tinyurl_api = settings.TINY_URL_API
dead_body_match_public_report = (
    settings.TEMPLATEID_ALERT_OC_DEAD_BODY_MATCH_WITH_PUBLIC_COMPLAINT
)


def shorten_url(url):
    url_tiny = f"https://tinyurl.com/api-create.php?apikey={tinyurl_api}&url={url}"
    response = requests.get(url_tiny)
    link = response.text
    return link


@app.task(task_soft_time_limit=3000, ignore_result=True)
def add_icon_to_report(pk):
    report = Report.objects.get(pk=pk)
    with Image.open(report.photo) as image:
        # Create resized image
        image.thumbnail((64, 64))

        # Create a BytesIO buffer to receive image data
        buffer = BytesIO()

        # Save the image to the buffer
        image.save(buffer, "JPEG")

        try:  # For production
            ACCESS_ID = settings.AWS_ACCESS_KEY_ID
            ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY

            # Create a new S3 client
            s3 = boto3.client(
                "s3", aws_access_key_id=ACCESS_ID, aws_secret_access_key=ACCESS_KEY
            )
            # Get the file name of the resized image
            icon_file_name = "icons_" + report.photo.name.split("/")[-1]

            # Get the contents of the buffer
            icon_data = buffer.getvalue()

            # Upload the resized image to S3
            s3.upload_fileobj(BytesIO(icon_data), "wb-missing-found", icon_file_name)

            # Save the file name of the resized image to the icon field of the model
            report.icon = icon_file_name
            report.save()
        except Exception as e:
            print(str(e))
            icon_file_name = "icons_" + report.photo.name.split("/")[-1]
            icon_file = InMemoryUploadedFile(
                buffer, None, icon_file_name, "image/jpeg", sys.getsizeof(buffer), None
            )
            report.icon = icon_file
            report.save()


@app.task(task_soft_time_limit=3000, ignore_result=True)
def add_description_search_vector_to_report(pk):
    report = Report.objects.get(pk=pk)
    print("adding DSV")
    report.description_search_vector = SearchVector("description")
    print(report.description_search_vector)
    report.save()


@app.task(task_soft_time_limit=3000, ignore_result=True)
def send_matched_mail(pk):
    match = Match.objects.get(pk=pk)
    if match.match_is_correct is None:
        report_missing = match.report_missing
        ps_missing = report_missing.police_station.ps_with_distt
        oc_missing = report_missing.police_station.officer_in_charge
        oc_missing_tel = report_missing.police_station.telephones
        oc_missing_email = report_missing.police_station.emails
        reference_missing = (
            str(report_missing.reference)
            + " dt. "
            + report_missing.entry_date.strftime("%d,%b,%Y")
        )
        name_missing = report_missing.name

        report_found = match.report_found
        ps_found = report_found.police_station.ps_with_distt
        oc_found = report_found.police_station.officer_in_charge
        oc_found_tel = report_found.police_station.telephones
        oc_found_email = report_found.police_station.emails
        reference_found = (
            str(report_found.reference)
            + " dt. "
            + report_found.entry_date.strftime("%d,%b,%Y")
        )

        # Shorten Links:
        report_found_url = (
            f"https://wbmissingfound.com/backend/view_report/{report_found.pk}/"
        )
        report_missing_url = (
            f"https://wbmissingfound.com/backend/view_report/{report_missing.pk}/"
        )
        # report_found_url_tiny_link = shorten_url(report_found_url)
        # report_missing_url_tiny_link = shorten_url(report_missing_url)

        message = (
            "Match for unidentified dead body: "
            + f"{report_found_url} . GoWB"
        )
        try:
            missing_message = (
                f"There is a match for missing person {name_missing} of your Police Station"
                + f" ref: {reference_missing} in {ps_missing}. See {report_missing_url}"
                + "\n"
                + f"Please contact the O/C {oc_found} regarding their PS Ref: {reference_found}. See {report_found_url}"
                + "\n"
                + f"Contact details are Tel:  {oc_found_tel} and Email: {oc_found_email}"
            )
            send_mail(
                "Missing Person Matched with Dead Body",
                missing_message,
                None,
                [oc_missing_email],
                fail_silently=False,
            )

            for user in User.objects.filter(
                category="DISTRICT_ADMIN",
                district=report_missing.police_station.district,
            ):
                send_mail(
                    "Missing Person Matched with Dead Body",
                    missing_message,
                    None,
                    [user.email],
                    fail_silently=False,
                )
            found_message = (
                f"There is a match for an unidentified dead body reported by you vide  {reference_found}"
                + f" of {ps_found} at {ps_missing}. See {report_found_url}"
                + "\n"
                + f"Please contact the O/C {oc_missing} regarding their PS Ref: {reference_missing}."
                + f" See {report_found_url}"
                + "\n"
                + f"Contact details are Tel: {oc_missing_tel} and Email: {oc_missing_email}"
            )
            send_mail(
                "Unidentified Dead Body Matched with Missing Person",
                found_message,
                None,
                [oc_found_email],
                fail_silently=False,
            )
            # To sanjay Singh
            send_mail(
                "Missing Person Matched with Dead Body",
                message,
                None,
                ["sanjaysingh13@gmail.com"],
                fail_silently=False,
            )
            for user in User.objects.filter(
                category="DISTRICT_ADMIN",
                district=report_found.police_station.district,
            ):
                send_mail(
                    "Unidentified Dead Body Matched with Missing Person",
                    found_message,
                    None,
                    [user.email],
                    fail_silently=False,
                )
                try:
                    send_sms(template_match, message, user.telephone)
                except Exception as e:
                    print(str(e))

            match.mail_sent = date.today()
            match.save()
            # Send SMSs
            telephones = [oc_missing_tel, oc_found_tel, "9830425757"]
            for telephone in telephones:
                if telephone:
                    try:
                        send_sms(template_match, message, telephone)
                    except Exception as e:
                        print(str(e))

        except Exception as e:
            print(str(e))


@app.task(task_soft_time_limit=3000, ignore_result=True)
def send_public_report_matched_mail(pk):
    match = PublicReportMatch.objects.get(pk=pk)
    report_missing = match.report_missing
    ps_missing = match.report_missing.police_station.ps_with_distt
    oc_missing = match.report_missing.police_station.officer_in_charge
    oc_missing_tel = match.report_missing.police_station.telephones
    oc_missing_email = report_missing.police_station.emails
    reference_missing = (
        str(report_missing.telephone_of_reporter)
        + " on "
        + report_missing.entry_date.strftime("%d,%b,%Y")
    )
    name_missing = report_missing.name

    report_found = match.report_found
    ps_found = match.report_found.police_station.ps_with_distt
    oc_found = match.report_found.police_station.officer_in_charge
    oc_found_tel = match.report_found.police_station.telephones
    oc_found_email = report_found.police_station.emails
    reference_found = (
        str(report_found.reference)
        + " dt. "
        + report_missing.entry_date.strftime("%d,%b,%Y")
    )
    report_found_url = (
        f"https://wbmissingfound.com/backend/view_report/{report_found.pk}/"
    )
    # report_found_url_tiny_link = shorten_url(report_found_url)
    message = (
        "There is a match for an unidentified dead body"
        + f" reported by you {report_found_url}. GoWB "

    )
    try:
        missing_message = (
            f"There is a match for missing person {name_missing} of your Police Station"
            + f" reported by public from tel: {reference_missing} in {ps_missing}."
            + f"Please contact the O/C {oc_found} regarding their PS Ref: {reference_found}. See {report_found_url}"
            + "\n"
            + f"Contact details are Tel:  {oc_found_tel} and Email: {oc_found_email}"
        )
        send_mail(
            "Missing Person Matched with Dead Body",
            missing_message,
            None,
            [oc_missing_email],
            fail_silently=False,
        )
        found_message = (
            f"There is a match for an unidentified dead body reported by you vide  {reference_found}"
            + f" of {ps_found} at {ps_missing}. See {report_found_url}"
            + "\n"
            + f"Please contact the O/C {oc_missing} regarding a public missing reported by: {reference_missing}."
            + "\n"
            + f"Contact details are Tel: {oc_missing_tel} and Email: {oc_missing_email}"
        )
        send_mail(
            "Unidentified Dead Body Matched with Missing Person",
            found_message,
            None,
            [oc_found_email],
            fail_silently=False,
        )
        # SMSs
        telephones = [oc_missing_tel, oc_found_tel, "9830425757"]
        for telephone in telephones:
            if telephone:
                try:
                    send_sms(dead_body_match_public_report, message, telephone)
                except Exception as e:
                    print(str(e))
        for user in User.objects.filter(
            category="DISTRICT_ADMIN",
            district=report_found.police_station.district,
        ):
            send_mail(
                "Unidentified Dead Body Matched with Missing Person",
                found_message,
                None,
                [user.email],
                fail_silently=False,
            )
        for user in User.objects.filter(
            category="DISTRICT_ADMIN",
            district=report_missing.police_station.district,
        ):
            send_mail(
                "Missing Person Matched with Dead Body",
                missing_message,
                None,
                [user.email],
                fail_silently=False,
            )
            try:
                send_sms(dead_body_match_public_report, message, user.telephone)
            except Exception as e:
                print(str(e))
        match.mail_sent = date.today()
        match.save()
    except Exception as e:
        print(str(e))


@app.task(task_soft_time_limit=300, ignore_result=True)
def send_public_report_created_mail(pk):
    report = PublicReport.objects.get(pk=pk)
    token_message = (
        "Your token for missing person "
        + f"{report.name}"
        + " reported by you on WB Mising Found is "
        + f"{report.token}"
    )

    alert_oc_message = (
        "A Public missing report has been filed in your jurisdiction. "
        + "Please visit "
        + f"https://wbmissingfound.com/backend/view_public_report/{report.token}/"
        + f" and contact the person at {report.telephone_of_reporter}."
    )
    send_mail(
        "Your token for missing person reported by you on WB Mising Found",
        token_message,
        None,
        [report.email_of_reporter],
        fail_silently=False,
    )
    # SMS
    message = f"Your token for missing person {report.name} is {report.token}. GoWB"
    try:
        send_sms(generate_token, message, report.telephone_of_reporter)
    except Exception as e:
        print(str(e))

    send_mail(
        "Public Missing Report on WB Mising Found",
        alert_oc_message,
        None,
        [report.police_station.emails],
        fail_silently=False,
    )
    send_mail(
        "Public Missing Report on WB Mising Found",
        alert_oc_message,
        None,
        ["sanjaysingh13@gmail.com"],
        fail_silently=False,
    )
    # SMSs
    message = (
        "A Public missing report has been filed. "
        + f"https://wbmissingfound.com/backend/view_public_report/{report.token}/ "
        + f"and contact {report.telephone_of_reporter}. GoWB"
    )

    telephones = [report.police_station.telephones, "9830425757"]
    for telephone in telephones:
        if telephone:
            try:
                send_sms(alert_oc_public_complaint, message, telephone)
            except Exception as e:
                print(str(e))

    for user in User.objects.filter(
        category="DISTRICT_ADMIN", district=report.police_station.district
    ):
        send_mail(
            "Public Missing Report on WB Mising Found",
            alert_oc_message,
            None,
            [user.email],
            fail_silently=False,
        )
        try:
            send_sms(alert_oc_public_complaint, message, user.telephone)
        except Exception as e:
            print(str(e))


@app.task
def send_summary_mail(task_soft_time_limit=300, ignore_result=True):
    now = timezone.now()

    last_24_hours = now - timezone.timedelta(hours=24)

    report_count = Report.objects.filter(created__gte=last_24_hours).aggregate(
        Count("id")
    )
    public_report_count = PublicReport.objects.filter(
        created__gte=last_24_hours
    ).aggregate(Count("id"))
    matches_count = Match.objects.filter(created__gte=last_24_hours).aggregate(
        Count("id")
    )
    users_count = User.objects.filter(last_login__gte=last_24_hours).aggregate(
        Count("id")
    )
    correct_matches_count = Match.objects.filter(
        modified__gte=last_24_hours, match_is_correct=True
    ).aggregate(Count("id"))

    send_mail(
        f"Activity summary Mising Found for {now.strftime('%Y-%m-%d')}",
        f"""
            Reports Added : {report_count}
            Public Reports Added : {public_report_count}
            Matches  Made : {matches_count}
            Coorect Matches: {correct_matches_count}
            Users Visited : {users_count}
            """,
        None,
        ["sanjaysingh13@gmail.com"],
        fail_silently=False,
    )


@app.task(task_soft_time_limit=300, ignore_result=True)
def send_sms(templateid, message, mobile):
    mobile = mobile[-10:]
    params = {
        "mobile": mobile,
        "templateid": templateid,
        "extra": "",
        "passkey": passkey,
        "message": message,
    }
    url = "http://barta.wb.gov.in/send_sms_ignb.php"
    response = requests.post(url, params=params)
    utc = parse(response.headers["Date"])
    to_zone = tz.gettz("Asia/Kolkata")
    local = utc.astimezone(to_zone)
    sms = Message(telephone=mobile, time=local, message=message)
    sms.save()
