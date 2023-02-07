import sys
from datetime import date
from io import BytesIO

import boto3
from django.conf import settings
from django.contrib.postgres.search import SearchVector
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.mail import send_mail
from PIL import Image

from config.celery_app import app
from missing_persons_match_unidentified_dead_bodies.backend.models import (
    Match,
    PublicReport,
    PublicReportMatch,
    Report,
)


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
    report_missing = match.report_missing
    ps_missing = match.report_missing.police_station.ps_with_distt
    oc_missing = match.report_missing.police_station.officer_in_charge
    oc_missing_tel = match.report_missing.police_station.telephones
    oc_missing_email = report_missing.police_station.emails
    reference_missing = (
        str(report_missing.reference)
        + " dt. "
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
    try:
        missing_message = (
            f"There is a match for missing person {name_missing} of your Police Station"
            + f" ref: {reference_missing} in {ps_missing}."
            + "\n"
            + f"Please contact the O/C {oc_found} regarding their PS Ref: {reference_found}."
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
            + f" of {ps_found} at {ps_missing}."
            + "\n"
            + f"Please contact the O/C {oc_missing} regarding their PS Ref: {reference_missing}."
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
        match.mail_sent = date.today()
        match.save()
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
    try:
        missing_message = (
            f"There is a match for missing person {name_missing} of your Police Station"
            + f" reported by public from tel: {reference_missing} in {ps_missing}."
            + "\n"
            + f"Please contact the O/C {oc_found} regarding their PS Ref: {reference_found}."
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
            + f" of {ps_found} at {ps_missing}."
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
        + " reported by you on WB Khoya Paya is "
        + f"{report.token}"
    )

    alert_oc_message = (
        "A Public missing report has been filed in your jurisdiction. "
        + "Please visit "
        + f"https://wwww.wbkhoyapaya/backend/view_public_report/{report.token}/"
        + f" and contact the person at {report.telephone_of_reporter}."
    )
    send_mail(
        "Your token for missing person reported by you on WB Khoya Paya",
        token_message,
        None,
        [report.email_of_reporter],
        fail_silently=False,
    )
    send_mail(
        "Public Missing Report on WB Khoya Paya",
        alert_oc_message,
        None,
        [report.police_station.emails],
        fail_silently=False,
    )
