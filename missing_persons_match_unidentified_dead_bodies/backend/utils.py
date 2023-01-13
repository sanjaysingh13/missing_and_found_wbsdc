from io import BytesIO

import cv2
import numpy as np
from django.core.files.uploadedfile import InMemoryUploadedFile


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
