# app/routes/redirect.py
import os
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
        # check for uuid in database here
        return redirect(os.getenv("NEXT_FORM_URL"), code=302)
    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": str(e)}), 500
