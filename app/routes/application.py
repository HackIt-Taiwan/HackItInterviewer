# app/routes/webhook.py
from flask import Blueprint, jsonify, request
# from app.discord.application_process.helpers import send_initial_embed, get_bot
# import asyncio

# from app.utils.mail_sender import send_email

application_bp = Blueprint('application', __name__)
# bot = get_bot()

# TODO: should not use hardcoded values
field_mapping = {
    'S5jaJPUkBIkt': '你的名字',
    'ApY1CyoJF6Rv': '電子郵件',
    '52lBVg2N0KoU': '電話號碼',
    'P7YquMjBAMb6': '高中階段',
    '1yLzipGL8CXc': '你住在哪',
    'umigMKtao9y7': '來找找適合你的領域',
    '': '為什麼想加入',
    'bdXbCUl1iiqq': '有什麼相關經驗或技能嗎',
    '2Etw3QvT5GT8': '是否同意我們蒐集並使用您的資料（簽名）'
}

high_school_stage_mapping = {
    'FfKX9DzFyPO5': '高一',
    'XLyjhSereJYK': '高二',
    'N3nMDkxAPFVa': '高三',
    'Dm3tO8L5RItg': '其他'
}

interested_fields_mapping = {
    'HDDzjo46UCML': '公關組',
    'BryEnikchCiP': '活動企劃組',
    'QTBS6ThhjimL': '美術組',
    'CL3C1UBMmCpy': '資訊組',
    'LMAYGT8Xo4zc': '影音組'
}

anti = []


@application_bp.route('/first_part_application', methods=['POST'])
def webhook():
    try:
        form_data = request.json.get('answers', [])

        # name = email = phone_number = high_school_stage = city = preferred_order = reason_for_choice = related_experience = signature_url = None
        # interested_fields = []
        #
        # # Parse form data
        # for answer in form_data:
        #     field_id = answer.get('id')
        #     field_value = answer.get('value')
        #
        #     match field_id:
        #         case 'S5jaJPUkBIkt':  # name
        #             name = field_value
        #         case 'ApY1CyoJF6Rv':  # email
        #             email = field_value
        #         case '52lBVg2N0KoU':  # phone number
        #             phone_number = field_value
        #         case 'P7YquMjBAMb6':  # high school stage
        #             if isinstance(field_value, dict):
        #                 stage_id = field_value.get('value', [None])[0]
        #                 high_school_stage = high_school_stage_mapping.get(stage_id, stage_id)
        #         case '1yLzipGL8CXc':  # city
        #             city = field_value
        #         case 'umigMKtao9y7':  # interested fields
        #             interested_field_ids = field_value.get('value', []) if isinstance(field_value, dict) else []
        #             interested_fields = [interested_fields_mapping.get(field_id, field_id) for field_id in interested_field_ids]
        #         case '3DqecY2ogvR5':  # preferred order
        #             preferred_order = field_value
        #         case 'fV33uN18Aq5b':  # reason for choice
        #             reason_for_choice = field_value
        #         case 'bdXbCUl1iiqq':  # related experience
        #             related_experience = field_value
        #         case '2Etw3QvT5GT8':  # signature URL
        #             signature_url = field_value

        # Replace this with backend_endpoint api
        # email_hash = hash_data(email)
        # is_duplicate = FormResponse.objects(email_hash=email_hash).first() is not None

        # print("---------------------------------")
        # print(f'Parsed form data: {name}, {email}, {phone_number}, {high_school_stage}, {city}, {interested_fields}, '
        #       f'{preferred_order}, {reason_for_choice}, {related_experience}, {signature_url}')
        print(form_data)

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

        return jsonify({'status': 'ok'})
    except Exception as e:
        print(e)
        return jsonify({'status': 'error', 'message': str(e)}), 500
