# app/utils/jwt.py
import os
import jwt
from datetime import datetime, timedelta


def generate_jwt_token(uuid):
    encoded_jwt = jwt.encode(
        {
            "sub": uuid,
            "exp": datetime.now() + timedelta(minutes=15),
        },
        os.getenv("JWT_SECRET_KEY"),
        algorithm="HS256",
    )

    return encoded_jwt


def parse_token(token):
    """
    Tries to decode a jwt token
    if success returns: True, uuid to next form
    else returns False
    """
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"])
        return True, payload["sub"]
    except jwt.ExpiredSignatureError:
        return False, ""
    except jwt.InvalidTokenError:
        return False, ""
