# app/routes/application.py
import os
import uuid
import asyncio
import requests

from datetime import datetime
from flask import Blueprint, jsonify, request
from app.discord.application_process.helpers import send_initial_embed, get_bot

from app.utils.jwt import parse_token
from app.utils.image import image_url_to_base64

application_bp = Blueprint("application", __name__)
bot = get_bot()

# Stage one
field_mapping = {
    "Name": os.getenv("FIELD_NAME"),
    "Email": os.getenv("FIELD_EMAIL"),
    "Phone": os.getenv("FIELD_PHONE"),
    "HighSchoolStage": os.getenv("FIELD_HIGH_SCHOOL_STAGE"),
    "City": os.getenv("FIELD_CITY"),
    "InterestedFields": os.getenv("FIELD_INTERESTED_FIELDS"),
    "Introduction": os.getenv("FIELD_INTRODUCTION"),
}

high_school_stage_mapping = {
    os.getenv("HIGH_SCHOOL_STAGE_1"): "高一",
    os.getenv("HIGH_SCHOOL_STAGE_2"): "高二",
    os.getenv("HIGH_SCHOOL_STAGE_3"): "高三",
    os.getenv("HIGH_SCHOOL_STAGE_4"): "高中以上",
}

interested_fields_mapping = {
    os.getenv("INTERESTED_FIELD_1"): "行政部",
    os.getenv("INTERESTED_FIELD_2"): "公共事務部",
    os.getenv("INTERESTED_FIELD_3"): "策劃部",
    os.getenv("INTERESTED_FIELD_4"): "媒體影像部",
    os.getenv("INTERESTED_FIELD_5"): "資訊科技部",
}

# Stage two
field_mapping_two = {
    "Nickname": os.getenv("FIELD_TWO_NICKNAME"),
    "OfficialEmail": os.getenv("FIELD_TWO_OFFICIAL_EMAIL"),
    "SchoolName": os.getenv("FIELD_TWO_SCHOOL_NAME"),
    "NationalID": os.getenv("FIELD_TWO_NATIONAL_ID"),
    "EmergencyContactName": os.getenv("FIELD_TWO_EMERGENCY_CONTACT_NAME"),
    "EmergencyContactPhone": os.getenv("FIELD_TWO_EMERGENCY_CONTACT_PHONE"),
    "EmergencyContactRelationship": os.getenv(
        "FIELD_TWO_EMERGENCY_CONTACT_RELATIONSHIP"
    ),
    "EmergencyContactName2": os.getenv("FIELD_TWO_EMERGENCY_CONTACT_NAME2"),
    "EmergencyContactPhone2": os.getenv("FIELD_TWO_EMERGENCY_CONTACT_PHONE2"),
    "EmergencyContactRelationship2": os.getenv(
        "FIELD_TWO_EMERGENCY_CONTACT_RELATIONSHIP2"
    ),
    "StudentIDFront": os.getenv("FIELD_TWO_STUDENT_ID_FRONT"),
    "StudentIDBack": os.getenv("FIELD_TWO_STUDENT_ID_BACK"),
    "IDCardFront": os.getenv("FIELD_TWO_ID_CARD_FRONT"),
    "IDCardBack": os.getenv("FIELD_TWO_ID_CARD_BACK"),
}

hidden_value_secret = os.getenv("HIDDEN_VALUE_SECRET")


@application_bp.route("/first_part_application", methods=["POST"])
def first_part():
    try:
        form_data = request.json.get("answers", [])

        name = email = phone_number = high_school_stage = city = national_id = (
            introduction
        ) = None
        interested_fields = []

        # Parse form data
        for answer in form_data:
            field_id = answer.get("id")
            field_value = answer.get("value")

            if field_id == field_mapping.get("Name"):
                name = field_value
            elif field_id == field_mapping.get("Email"):
                email = field_value
            elif field_id == field_mapping.get("Phone"):
                phone_number = field_value
            elif field_id == field_mapping.get("HighSchoolStage"):
                if isinstance(field_value, dict):
                    stage_id = field_value.get("value", [None])[0]
                    high_school_stage = high_school_stage_mapping.get(
                        stage_id, stage_id
                    )
            elif field_id == field_mapping.get("City"):
                city = field_value
            elif field_id == field_mapping.get("InterestedFields"):
                interested_field_ids = (
                    field_value.get("value", [])
                    if isinstance(field_value, dict)
                    else []
                )
                interested_fields = [
                    interested_fields_mapping.get(field_id, field_id)
                    for field_id in interested_field_ids
                ]
            elif field_id == field_mapping.get("Introduction"):
                introduction = field_value

        print("---------------------------------")
        print(
            f"Parsed form data: {name}, {email}, {phone_number}, {high_school_stage}, {city}, {interested_fields[0]}, {introduction}"
        )

        user_uuid = str(uuid.uuid4())

        form_response = {
            "uuid": user_uuid,
            "real_name": name,
            "email": email,
            "official_email": "placeholder@hackit.tw",  # we'll overwrite this later
            "phone_number": "0"
            + phone_number[4:],  # database required phone number without prefix
            "high_school_stage": high_school_stage,
            "city": city,
            "introduction": introduction,
            "emergency_contact": [
                {
                    "name": "np",
                    "phone": "1234567890",
                    "relationship": "close",
                }  # we'll overwrite this later as well
            ],
            "current_group": interested_fields[0],
            "permission_level": 10,
        }

        headers = {"Authorization": f"Bearer {os.getenv('AUTH_TOKEN', '')}"}

        # Saves to database

        response = requests.post(
            url=f"{os.getenv("BACKEND_ENDPOINT")}/staff/create/new",
            headers=headers,
            json=form_response,
        )

        if response.status_code != 201:
            print(response.text)
            return jsonify({"status": "error", "message": "Bad request"}), 400

        # Sends to discord

        future = asyncio.run_coroutine_threadsafe(
            send_initial_embed(form_response), bot.loop
        )
        future.result()

        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": str(e)}), 500


@application_bp.route("/second_part_application", methods=["POST"])
def second_part():
    try:
        form_data = request.json.get("answers", [])
        hidden_values = request.json.get("hiddenFields", [])

        nickname = official_email = school = emergency_contact_name = (
            emergency_contact_phone
        ) = emergency_contact_relationship = emergency_contact_name2 = (
            emergency_contact_phone2
        ) = emergency_contact_relationship2 = studentidfront = studentidback = (
            idcard_front
        ) = idcard_back = token = None

        for answer in form_data:
            field_id = answer.get("id")
            field_value = answer.get("value")

            if field_id == field_mapping_two.get("Nickname"):
                nickname = field_value
            elif field_id == field_mapping_two.get("OfficialEmail"):
                official_email = field_value
            elif field_id == field_mapping_two.get("SchoolName"):
                school = field_value
            elif field_id == field_mapping_two.get("NationalID"):
                national_id = field_value
            elif field_id == field_mapping_two.get("EmergencyContactName"):
                emergency_contact_name = field_value
            elif field_id == field_mapping_two.get("EmergencyContactPhone"):
                emergency_contact_phone = "0" + field_value[4:]
            elif field_id == field_mapping_two.get("EmergencyContactRelationship"):
                emergency_contact_relationship = field_value
            elif field_id == field_mapping_two.get("EmergencyContactName2"):
                emergency_contact_name2 = field_value
            elif field_id == field_mapping_two.get("EmergencyContactPhone2"):
                emergency_contact_phone2 = "0" + field_value[4:]
            elif field_id == field_mapping_two.get("EmergencyContactRelationship2"):
                emergency_contact_relationship2 = field_value
            elif field_id == field_mapping_two.get("StudentIDFront"):
                studentidfront = image_url_to_base64(field_value.get("url"))
                if not studentidfront:
                    return jsonify({"status": "error", "message": "Bad request"}), 400
            elif field_id == field_mapping_two.get("StudentIDBack"):
                studentidback = image_url_to_base64(field_value.get("url"))
                if not studentidfront:
                    return jsonify({"status": "error", "message": "Bad request"}), 400
            elif field_id == field_mapping_two.get("IDCardFront"):
                idcard_front = image_url_to_base64(field_value.get("url"))
                if not studentidfront:
                    return jsonify({"status": "error", "message": "Bad request"}), 400
            elif field_id == field_mapping_two.get("IDCardBack"):
                idcard_back = image_url_to_base64(field_value.get("url"))
                if not studentidfront:
                    return jsonify({"status": "error", "message": "Bad request"}), 400

        for data in hidden_values:
            field_id = data.get("id")
            field_value = data.get("value")

            if field_id == hidden_value_secret:
                token = field_value

        print("---------------------------------")
        print(
            f"Parsed form data: {nickname}, {official_email}, {school}, {national_id}, {emergency_contact_name}, {emergency_contact_name2}"
        )

        headers = {"Authorization": f"Bearer {os.getenv('AUTH_TOKEN', '')}"}

        if not token:
            return jsonify({"status": "error", "message": "Bad request"}), 400

        is_valid, uuid = parse_token(token)

        if not is_valid or uuid == "":
            return jsonify({"status": "error", "message": "Bad request"}), 400

        # Saves to database

        form_response = {
            "nickname": nickname,
            "official_email": official_email,
            "school": school,
            "national_id": national_id,
            "permission_level": 6,
            "student_card": [
                {
                    "front": studentidfront,
                    "back": studentidback,
                }
            ],
            "id_card": [
                {
                    "front": idcard_front,
                    "back": idcard_back,
                }
            ],
            "emergency_contact": [
                {
                    "name": emergency_contact_name,
                    "phone": emergency_contact_phone,
                    "relationship": emergency_contact_relationship,
                },
                {
                    "name": emergency_contact_name2,
                    "phone": emergency_contact_phone2,
                    "relationship": emergency_contact_relationship2,
                },
            ],
        }

        response = requests.post(
            url=f"{os.getenv("BACKEND_ENDPOINT")}/staff/update/{uuid}",
            headers=headers,
            json=form_response,
        )

        if response.status_code != 200:
            print(response.text)
            return jsonify({"status": "error", "message": "Bad request"}), 400

        return jsonify({"status": "ok"})
    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": str(e)}), 500


@application_bp.route("/testing", methods=["POST"])
def testing():
    try:
        form_data = request.json.get("hiddenFields", [])
        print(form_data)
        form_data = request.json.get("answers", [])
        print(form_data)
        return jsonify({"status": "ok"})
    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": str(e)}), 500
