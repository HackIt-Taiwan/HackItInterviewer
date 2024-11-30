# app/utils/image.py
import base64
import mimetypes
import requests


def image_url_to_base64(image_url):
    response = requests.get(image_url)

    if response.status_code != 200:
        return False

    mime_type, _ = mimetypes.guess_type(image_url)
    if not mime_type or not mime_type.startswith('image/'):
        return False

    base64_encoded = base64.b64encode(response.content).decode("utf-8")

    return base64_encoded
