# app/routes/webhook.py
from flask import Blueprint, jsonify, request
# from app.discord.application_process.helpers import send_initial_embed, get_bot
# import asyncio

# from app.utils.mail_sender import send_email

application_bp = Blueprint("application", __name__)
# bot = get_bot()

# TODO: should not use hardcoded values
field_mapping = {
    "XLAq7Uwzn4Ep": "你的名字",
    "TuQZE7sL16sM": "電子郵件",
    "y8oWYKyZ4rNr": "電話號碼",
    "LGZHt3lgqE9K": "高中階段",
    "XoVZX9MD8Z3N": "你住在哪",
    "bent6BusJh3O": "來找找適合你的領域",
    "3wO2nn8p6kQ7": "為什麼想加入",
    "AJacPbdzNn57": "有什麼相關經驗或技能嗎",
    # "2Etw3QvT5GT8": "是否同意我們蒐集並使用您的資料（簽名）",
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

anti = []


@application_bp.route("/first_part_application", methods=["POST"])
def webhook():
    try:
        form_data = request.json.get("answers", [])

        name = email = phone_number = high_school_stage = city = reason = (
            related_experience
        ) = None
        interested_fields = []

        # Parse form data
        for answer in form_data:
            field_id = answer.get("id")
            field_value = answer.get("value")

            match field_id:
                case "XLAq7Uwzn4Ep":  # name
                    name = field_value
                case "TuQZE7sL16sM":  # email
                    email = field_value
                case "y8oWYKyZ4rNr":  # phone number
                    phone_number = field_value
                case "LGZHt3lgqE9K":  # high school stage
                    if isinstance(field_value, dict):
                        stage_id = field_value.get("value", [None])[0]
                        high_school_stage = high_school_stage_mapping.get(
                            stage_id, stage_id
                        )
                case "XoVZX9MD8Z3N":  # city
                    city = field_value
                case "bent6BusJh3O":  # interested fields
                    interested_field_ids = (
                        field_value.get("value", [])
                        if isinstance(field_value, dict)
                        else []
                    )
                    interested_fields = [
                        interested_fields_mapping.get(field_id, field_id)
                        for field_id in interested_field_ids
                    ]
                case "3wO2nn8p6kQ7":  # reason for choice
                    reason = field_value
                case "AJacPbdzNn57":  # related experience
                    related_experience = field_value

        # Replace this with backend_endpoint api
        # email_hash = hash_data(email)
        # is_duplicate = FormResponse.objects(email_hash=email_hash).first() is not None

        print("---------------------------------")
        print(
            f"Parsed form data: {name}, {email}, {phone_number}, {high_school_stage}, {city}, {interested_fields}, {reason}, {related_experience}"
        )

        # form_response = FormResponse(
        #     name=name,
        #     email=email,
        #     phone_number=phone_number,
        #     high_school_stage=high_school_stage,
        #     city=city,
        #     interested_fields=interested_fields,
        #     preferred_order=preferred_order,
        #     reason_for_choice=reason_for_choice,
        #     related_experience=related_experience,
        #     signature_url=signature_url,
        # )
        #
        # form_response.save()
        # future = asyncio.run_coroutine_threadsafe(send_initial_embed(form_response), bot.loop)
        # future.result()  # This will block until the coroutine finishes and raise exceptions if any

        # send_email(
        #     subject="Counterspell / 已收到您的工作人員報名表！",
        #     recipient=email,
        #     template='emails/notification_email.html',
        #     name=name,
        #     uuid=form_response.uuid
        # )

        return jsonify({"status": "ok"})
    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": str(e)}), 500


@application_bp.route("/")
def testing():
    return "itworks"
