# app/discord/import_existing_members/helpers.py
import json
import os

from app.models.staff import Staff
from app.utils.redis_client import redis_client

EXECUTOR_DISCORD_ID = os.getenv("EXECUTOR_DISCORD_ID")


def get_user_data(user_id):
    """Retrieve user data from Redis."""
    data = redis_client.get(f"user_data:{user_id}")
    if data:
        return json.loads(data)
    return {}


def set_user_data(user_id, data):
    """Store user data in Redis with an expiration time."""
    redis_client.set(f"user_data:{user_id}", json.dumps(data), ex=3600)


def has_submitted_form(user_id):
    """Check if the user has already submitted the form."""
    return (
        redis_client.exists(f"import_form_submitted:{user_id}")
        or Staff.objects(discord_user_id=str(user_id)).count() > 0
    )


def mark_form_as_submitted(user_id):
    """Mark the form as submitted for the user."""
    redis_client.set(f"import_form_submitted:{user_id}", "1")


def truncate(value, max_length=1024):
    """Truncate a string to the specified maximum length."""
    if len(value) > max_length:
        return value[: max_length - 80] + "...（太長，無法顯示）"
    return value
