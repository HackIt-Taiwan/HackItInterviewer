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
        payload = {"long_url": url, "exp": expiration_timestamp}
    else:
        payload = {"long_url": url}

    response = requests.post(
        os.getenv("SHORTEN_API_URL")+"/shorten", headers=headers, json=payload
    )

    if response.status_code != 200:
        return None

    return os.getenv("SHORTEN_API_TOKEN") + "/" + response.json()["short_url"]
