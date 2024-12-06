# app/utils/jwt.py
import os
import jwt
from datetime import datetime, timedelta


def generate_form_token(uuid):
    """
    Generates jwt token for verifying it is the applicant who's
    filling the second part form.
    """
    encoded_jwt = jwt.encode(
        {
            "sub": uuid,
            "exp": datetime.now() + timedelta(days=30),
        },
        os.getenv("JWT_SECRET_KEY"),
        algorithm="HS256",
    )

    return encoded_jwt

def generate_data_token(uuid):
    """
    This is for preventing unauthorized person reading applicant's data
    In the discord server.
    """
    encoded_jwt = jwt.encode(
        {
            "sub": uuid, # Maybe a 1 month exp?
        },
        os.getenv("JWT_SECRET_KEY"),
        algorithm="HS256",
    )
    return encoded_jwt



def parse_token(token, secret):
    """
    Tries to decode a jwt token
    if success returns: True, uuid to next form
    else returns False
    """
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return True, payload["sub"] # This returns the sub value, change if needed.
    except jwt.ExpiredSignatureError:
        return False, ""
    except jwt.InvalidTokenError:
        return False, ""


def generate_next_url(uuid):
    """Generate redirect url"""
    secret = generate_form_token(uuid)
    accept_url = f"{os.getenv("NEXT_FORM_URL")}?secret={secret}"

    return accept_url
