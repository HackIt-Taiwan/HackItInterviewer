# app/routes/application.py
import os
import jwt
import requests
# import asyncio

from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, make_response
# from app.discord.application_process.helpers import send_initial_embed, get_bot

from app.utils.crypto import generate_secret
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
    "StudentIDFront": "IEx5shdcXeud",
    "StudentIDBack": "QMmN5JoVFw9v",
    "IDCardFront": "1D6dprnfcU72",
    "IDCardBack": "QtDXmmGPVwcr",
}


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

        # Replace this with backend_endpoint api
        # email_hash = hash_data(email)
        # is_duplicate = FormResponse.objects(email_hash=email_hash).first() is not None

        print("---------------------------------")
        print(
            f"Parsed form data: {name}, {email}, {phone_number}, {high_school_stage}, {city}, {national_id}, {interested_fields[0]}, {introduction}"
        )

        secret = generate_secret()
        fixed_secret = secret + os.getenv("FIXED_JWT_SECRET")
        encoded_jwt = jwt.encode(
            {
                "sub": "79140886-47e3-4e20-8e98-7dfec71bdd65",  # change this later
                "exp": datetime.now() + timedelta(minutes=15),
            },
            fixed_secret,
            algorithm="HS256",
        )

        form_response = {
            "uuid": "79140886-47e3-4e20-8e98-7dfec71bdd65",  # change this later
            "name": name,
            "email": email,
            "official_email": "placeholder@staff.hackit.tw",  # we'll overwrite this later
            "phone_number": phone_number,
            "high_school_stage": high_school_stage,
            "city": city,
            "national_id": national_id,
            "introduction": introduction,
            "current_group": interested_fields[0],
            "permission_level": 1,
            "created_at": datetime.now().isoformat(),
        }

        # save to database and send discord here
        headers = {"Authorization": "Bearer " + os.getenv("AUTH_TOKEN")}

        requests.post(
            url=os.getenv("BACKEND_ENDPOINT") + "/staff/create/new",
            headers=headers,
            json=form_response,
        )

        # future = asyncio.run_coroutine_threadsafe(send_initial_embed(form_response), bot.loop)
        # future.result()  # This will block until the coroutine finishes and raise exceptions if any

        # accept_url = urlparse(
        #     scheme="https",  # Change to http for developing
        #     netloc=os.getenv("HOST") + ":" + os.getenv("PORT"),
        #     path="/redirect/check",
        #     params=secret,
        # )
        #
        # print(accept_url)

        # Stores JWT to cookie

        response = make_response(jsonify({"status": "ok"}))
        # response.set_cookie(
        #     "access_token",
        #     encoded_jwt,
        #     httponly=True,
        #     secure=True,  # setting to false for development
        #     samesite="Strict",
        # )
        return response
    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": str(e)}), 500


@application_bp.route("/second_part_application", methods=["POST"])
def second_part():
    try:
        form_data = request.json.get("answers", [])

        nickname = official_email = school = emergency_contact_name = (
            emergency_contact_phone
        ) = emergency_contact_relationship = studentidfront = studentidback = (
            idcard_front
        ) = idcard_back = None

        for answer in form_data:
            field_id = answer.get("id")
            field_value = answer.get("value")

            match field_id:
                case field_mapping_two.get("Nickname"):
                    nickname = field_value
                case field_mapping_two.get("OfficialEmail"):
                    official_email = field_value
                case field_mapping_two.get("SchoolName"):
                    school = field_value
                case field_mapping_two.get("EmergencyContactName"):
                    emergency_contact_name = field_value
                case field_mapping_two.get("EmergencyContactPhone"):
                    emergency_contact_phone = field_value
                case field_mapping_two.get("EmergencyContactRelationship"):
                    emergency_contact_relationship = field_value
                case field_mapping_two.get("StudentIDFront"):
                    url = field_value.get("url")

                    studentidfront = image_url_to_base64(url)
                    if not studentidfront:
                        raise Exception("Bad image")
                case field_mapping_two.get("StudentIDBack"):
                    url = field_value.get("url")

                    studentidback = image_url_to_base64(url)
                    if not studentidfront:
                        raise Exception("Bad image")
                case field_mapping_two.get("IDCardFront"):
                    url = field_value.get("url")

                    idcard_front = image_url_to_base64(url)
                    if not studentidfront:
                        raise Exception("Bad image")
                case field_mapping_two.get("IDCardBack"):
                    url = field_value.get("url")

                    idcard_back = image_url_to_base64(url)
                    if not studentidfront:
                        raise Exception("Bad image")

        print("---------------------------------")
        print(
            f"Parsed form data: {nickname}, {official_email}, {school}, {emergency_contact_name}, {studentidfront}, {idcard_front}"
        )

        # update to database here

        return jsonify({"status": "ok"})
    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": str(e)}), 500


@application_bp.route("/testing", methods=["POST"])
def testing():
    try:
        form_data = request.json.get("answers", [])

        print(form_data)

        return jsonify({"status": "ok"})
    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": str(e)}), 500
