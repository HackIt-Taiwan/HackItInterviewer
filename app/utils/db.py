# app/utils/db.py
import os
import requests


def get_staff(payload):
    headers = {"Authorization": f"Bearer {os.getenv('AUTH_TOKEN', '')}"}
    response = requests.post(
        url=f"{os.getenv("BACKEND_ENDPOINT")}/staff/getstaffs",
        headers=headers,
        json=payload,
    )

    if response.status_code != 200:
        return False, None
    return True, response


def update_staff(uuid, payload):
    headers = {"Authorization": f"Bearer {os.getenv('AUTH_TOKEN', '')}"}
    response = requests.post(
        url=f"{os.getenv("BACKEND_ENDPOINT")}/staff/update/{uuid}",
        headers=headers,
        json=payload,
    )

    if response.status_code != 200:
        return False
    return True
