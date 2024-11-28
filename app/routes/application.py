# app/routes/application.py
import os
import uuid
import requests
# import asyncio

from datetime import datetime
from flask import Blueprint, jsonify, request
# from app.discord.application_process.helpers import send_initial_embed, get_bot

from app.utils.jwt import generate_jwt_token, parse_token
from app.utils.image import image_url_to_base64

application_bp = Blueprint("application", __name__)
# bot = get_bot()

# TODO: should not use hardcoded values, move them to env
# Stage one
field_mapping = {
    "Name": "XLAq7Uwzn4Ep",
    "Email": "TuQZE7sL16sM",
    "Phone": "y8oWYKyZ4rNr",
    "HighSchoolStage": "LGZHt3lgqE9K",
    "City": "XoVZX9MD8Z3N",
    "NationalID": "sDE4W8PgEM3J",
    "InterestedFields": "bent6BusJh3O",
    "Introduction": "3wO2nn8p6kQ7",
    # "是否同意我們蒐集並使用您的資料（簽名）": "2Etw3QvT5GT8",
}

high_school_stage_mapping = {
    "QSPOLTPXkApB": "高一",
    "zgexoXDSh4L9": "高二",
    "SfNAXlu1qTyp": "高三",
    "bBzRtCawZbxR": "其他",
}

interested_fields_mapping = {
    "rxcqgScwZt6V": "策劃部",
    "nwZZ9T4hqm1D": "設計部",
    "i7yliEmglWWi": "行政部",
    "IDmmAQC3X8F3": "公關組",
    "ic9NIPSy7bSh": "活動企劃組",
    "lqGiREKp1i0y": "美術組",
    "SL2ZkegwrKoz": "資訊組",
    "qGzTbHgzUIvl": "影音組",
    "NbOhzLWQToSO": "行政組",
    "Q6lFRKR7QxR8": "財務組",
    "ltGHHif19TKf": "其他",
}

# Stage two
field_mapping_two = {
    "Nickname": "JBFg5bcpbBFX",
    "OfficialEmail": "BhIZEM4DEKIv",
    "SchoolName": "GirzXOm97pqz",
    "EmergencyContactName": "aOycU3YWHsnb",
    "EmergencyContactPhone": "K3XwYXb9QKLh",
    "EmergencyContactRelationship": "nUeuGr9JXoeA",
    "EmergencyContactName2": "test",
    "EmergencyContactPhone2": "test",
    "EmergencyContactRelationship2": "test",
    "StudentIDFront": "IEx5shdcXeud",
    "StudentIDBack": "QMmN5JoVFw9v",
    "IDCardFront": "1D6dprnfcU72",
    "IDCardBack": "QtDXmmGPVwcr",
}

hidden_value_secret = "hUm24WLc"


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
            elif field_id == field_mapping.get("NationalID"):
                national_id = field_value
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
            f"Parsed form data: {name}, {email}, {phone_number}, {high_school_stage}, {city}, {national_id}, {interested_fields[0]}, {introduction}"
        )

        user_uuid = str(uuid.uuid4())

        secret = generate_jwt_token(user_uuid)

        form_response = {
            "uuid": user_uuid,
            "real_name": name,
            "email": email,
            "official_email": "placeholder@hackit.tw",  # we'll overwrite this later
            "phone_number": "0"
            + phone_number[4:],  # database required phone number without prefix
            "high_school_stage": high_school_stage,
            "city": city,
            "national_id": national_id,
            "introduction": introduction,
            "emergency_contact": [
                {
                    "name": "np",
                    "phone": "1234567890",
                    "relationship": "close",
                }  # we'll overwrite this later as well
            ],
            "current_group": interested_fields[0],
            "permission_level": 1,
            "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        }

        headers = {"Authorization": f"Bearer {os.getenv('AUTH_TOKEN', '')}"}

        # Generate redirect url

        accept_url = f"{os.getenv("NEXT_FORM_URL")}?secret={secret}"
        print(accept_url)

        # Saves to database

        response = requests.post(
            url=f"{os.getenv("BACKEND_ENDPOINT")}/staff/create/new",
            headers=headers,
            json=form_response,
        )

        if response.status_code != 200:
            return jsonify({"status": "error", "message": "Bad request"}), 400

        # Sends to discord

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
            f"Parsed form data: {nickname}, {official_email}, {school}, {emergency_contact_name}, {emergency_contact_name2}"
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
