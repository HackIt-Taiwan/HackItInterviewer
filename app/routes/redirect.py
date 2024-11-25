# app/routes/redirect.py
import os
import requests
from flask import Blueprint, jsonify, request, redirect

from app.utils.crypto import parse_token

redirect_bp = Blueprint("redirect", __name__)


@redirect_bp.route("/check", methods=["GET"])
def redirect_check():
    try:
        secret = request.args.get("secret") + os.getenv("FIXED_JWT_SECRET")
        token = request.cookies.get("access_token")
        is_valid, uuid = parse_token(token, secret)
        if not is_valid:
            return jsonify({"status": "error", "message": "Bad Request"}), 400

        uuid_json = {"uuid": uuid}
        headers = {"Authorization": f"Bearer {os.getenv('AUTH_TOKEN', '')}"}

        response = requests.post(
            url=f"{os.getenv("BACKEND_ENDPOINT")}/staff/getstaffs",
            headers=headers,
            json=uuid_json,
        )
        if response.status_code != 200:
            return jsonify({"status": "error", "message": "Bad Request"}), 400

        return redirect(os.getenv("NEXT_FORM_URL"), code=302)
    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": str(e)}), 500
