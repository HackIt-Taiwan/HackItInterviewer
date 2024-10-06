# app/routes/webhook.py
from flask import Blueprint, jsonify, request
from app.models.form_response import FormResponse
from app.utils.encryption import hash_data
from app.discord.application_process.helpers import send_initial_embed, get_bot
import asyncio

webhook_bp = Blueprint('webhook', __name__)
bot = get_bot()

# TODO: should not use hardcoded values
field_mapping = {
    'S5jaJPUkBIkt': '你的名字',
    'ApY1CyoJF6Rv': '電子郵件',
    '52lBVg2N0KoU': '電話號碼',
    'P7YquMjBAMb6': '高中階段',
    '1yLzipGL8CXc': '你住在哪',
    'umigMKtao9y7': '來找找適合你的領域',
    '3DqecY2ogvR5': '排一排，告訴我們你的優先選擇吧',
    'fV33uN18Aq5b': '為什麼選擇這些組別',
    'bdXbCUl1iiqq': '有什麼相關經驗或技能嗎',
    'Gkg271OtI9Bw': '是否同意我們蒐集並使用您的資料（簽名）'
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


@webhook_bp.route('/webhook', methods=['POST'])
def webhook():
    with open('webhook_data.txt', 'w', encoding='utf-8') as f:
        f.write(str(request.json))

    # anti multiple submission
    email = request.json.get('answers', [{}])[1].get('value')
    if email in anti:
        return jsonify({'status': 'error', 'message': 'duplicate submission'}), 200
    anti.append(email)

    try:
        form_data = request.json.get('answers', [])

        name = email = phone_number = high_school_stage = city = preferred_order = reason_for_choice = related_experience = signature_url = None
        interested_fields = []

        # Parse form data
        for answer in form_data:
            field_id = answer.get('id')
            field_value = answer.get('value')

            match field_id:
                case 'S5jaJPUkBIkt':  # name
                    name = field_value
                case 'ApY1CyoJF6Rv':  # email
                    email = field_value
                case '52lBVg2N0KoU':  # phone number
                    phone_number = field_value
                case 'P7YquMjBAMb6':  # high school stage
                    if isinstance(field_value, dict):
                        stage_id = field_value.get('value', [None])[0]
                        high_school_stage = high_school_stage_mapping.get(stage_id, stage_id)
                case '1yLzipGL8CXc':  # city
                    city = field_value
                case 'umigMKtao9y7':  # interested fields
                    interested_field_ids = field_value.get('value', []) if isinstance(field_value, dict) else []
                    interested_fields = [interested_fields_mapping.get(field_id, field_id) for field_id in interested_field_ids]
                case '3DqecY2ogvR5':  # preferred order
                    preferred_order = field_value
                case 'fV33uN18Aq5b':  # reason for choice
                    reason_for_choice = field_value
                case 'bdXbCUl1iiqq':  # related experience
                    related_experience = field_value
                case 'Gkg271OtI9Bw':  # signature URL
                    signature_url = field_value

        email_hash = hash_data(email)
        is_duplicate = FormResponse.objects(email_hash=email_hash).first() is not None

        print(f'Parsed form data: {name}, {email}, {phone_number}, {high_school_stage}, {city}, {interested_fields}, '
              f'{preferred_order}, {reason_for_choice}, {related_experience}, {signature_url}, {email_hash}, {is_duplicate}')

        form_response = FormResponse(
            name=name,
            email=email,
            phone_number=phone_number,
            high_school_stage=high_school_stage,
            city=city,
            interested_fields=interested_fields,
            preferred_order=preferred_order,
            reason_for_choice=reason_for_choice,
            related_experience=related_experience,
            signature_url=signature_url,
            email_hash=email_hash,
            is_duplicate=is_duplicate
        )

        form_response.save()
        future = asyncio.run_coroutine_threadsafe(send_initial_embed(form_response), bot.loop)
        future.result()  # This will block until the coroutine finishes and raise exceptions if any


        return jsonify({'status': 'ok'})
    except Exception as e:
        print(e)
        return jsonify({'status': 'error', 'message': str(e)}), 500
