# app/routes/application.py
import os
import jwt

from urllib.parse import urlparse
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, make_response
# from app.discord.application_process.helpers import send_initial_embed, get_bot
# import asyncio

from app.utils.crypto import generate_secret

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
    "NationalID": "",
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
    "Nickname": "",
    "OfficialEmail": "",
    "SchoolName": "",
    "EmergencyContacts": "",
    "StudendIDs": "",
    "IDCards": "",
}

emergency_contact_mapping = {"test1": "名子", "test2": "關係", "test3": "手機號碼"}

student_card_mapping = {"test2": "正面", "test1": "反面"}

identification_card_mapping = {"test2": "正面", "test1": "反面"}


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

            match field_id:
                case field_mapping.get("Name"):  # name
                    name = field_value
                case field_mapping.get("Email"):
                    email = field_value
                case field_mapping.get("Phone"):
                    phone_number = field_value
                case field_mapping.get("HighSchoolStage"):
                    if isinstance(field_value, dict):
                        stage_id = field_value.get("value", [None])[0]
                        high_school_stage = high_school_stage_mapping.get(
                            stage_id, stage_id
                        )
                case field_mapping.get("City"):
                    city = field_value
                case field_mapping.get("NationalID"):
                    national_id = field_value
                case field_mapping.get("InterestedFields"):
                    interested_field_ids = (
                        field_value.get("value", [])
                        if isinstance(field_value, dict)
                        else []
                    )
                    interested_fields = [
                        interested_fields_mapping.get(field_id, field_id)
                        for field_id in interested_field_ids
                    ]
                case field_mapping.get("Introduction"):
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

        # form_response.save()
        # future = asyncio.run_coroutine_threadsafe(send_initial_embed(form_response), bot.loop)
        # future.result()  # This will block until the coroutine finishes and raise exceptions if any

        accept_url = urlparse(
            scheme="http",  # Change to http for developing
            netloc=os.getenv("HOST") + ":" + os.getenv("PORT"),
            path="/redirect/check",
            params=secret,
        )

        print(accept_url)

        # Stores JWT to cookie

        response = make_response(jsonify({"status": "ok"}))
        response.set_cookie(
            "access_token",
            encoded_jwt,
            httponly=True,
            secure=False,  # setting to false for development
            samesite="Strict",
        )
        return response
    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": str(e)}), 500


@application_bp.route("/second_part_application", methods=["POST"])
def second_part():
    try:
        form_data = request.json.get("answers", [])

        nickname, official_email = school = None
        emergency_contact = []
        studentcard = []
        idcard = []

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
                case field_mapping_two.get("EmergencyContacts"):
                    emergency_field_ids = (
                        field_value.get("value", [])
                        if isinstance(field_value, dict)
                        else []
                    )
                    emergency_contact = [
                        emergency_contact_mapping.get(field_id, field_id)
                        for field_id in emergency_field_ids
                    ]
                case field_mapping_two.get("StudendIDs"):
                    pass
                case field_mapping_two.get("IDCards"):
                    pass

        print("---------------------------------")
        print(
            f"Parsed form data: {nickname}, {official_email}, {school}, {emergency_contact}, {studentcard}, {idcard}"
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
