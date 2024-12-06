# app/utils/shortlink.py
import os
import requests

from datetime import datetime, timedelta


async def make_short_link(url, expiry_days):
    if expiry_days == 0 or None:
        expiration_timestamp = None
    else:
        expiration_date = datetime.utcnow() + timedelta(days=expiry_days)
        expiration_timestamp = int(expiration_date.timestamp())

    headers = {
        "Authorization": f'Bearer {os.getenv("SHORTEN_API_TOKEN")}',
        "Content-Type": "application/json",
    }
    if expiration_timestamp:
        payload = {"url": url, "expiration": expiration_timestamp}
    else:
        payload = {"url": url}

    response = requests.post(
        os.getenv("SHORTEN_API_URL"), headers=headers, json=payload
    )

    if response.status_code != 201:
        return None

    return "https://go.hackit.tw/" + response.json()["link"]["slug"]
