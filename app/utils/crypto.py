# app/utils/crypto.py
import jwt
import secrets


def generate_secret(length=16):
    # Generate a randomize string that's url safe
    secret = secrets.token_urlsafe(length)

    return secret


def parse_token(token, secret):
    """
    Tries to decode a jwt token
    if success returns: True, uuid, url to next form
    else returns False
    """
    try:
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        return True, payload['sub']
    except jwt.ExpiredSignatureError:
        return False, ""
    except jwt.InvalidTokenError:
        return False, ""
