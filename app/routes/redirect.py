# app/routes/redirect.py
from flask import Blueprint, jsonify, request

redirect_bp = Blueprint("redirect", __name__)

@redirect_bp.route("/check", methods=["GET"])
def redirect_check():
    return "sup"
