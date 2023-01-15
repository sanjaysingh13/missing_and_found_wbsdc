from io import BytesIO

import boto3
from django.conf import settings
from django.contrib.postgres.search import SearchVector
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image

from config.celery_app import app
from missing_persons_match_unidentified_dead_bodies.backend.models import Report, Token

from .utils import tokenize


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
                buffer, None, icon_file_name, "image/jpeg", len(buffer), None
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
def add_tokens_to_report(pk):
    report = Report.objects.get(pk=pk)
    tokens = tokenize(report.description)
    token_objects = []
    for token in tokens:
        (obj, created) = Token.objects.get_or_create(name=token)
        token_objects.append(obj)
    report.tokens.add(*token_objects)
