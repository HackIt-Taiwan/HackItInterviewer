# app/discord/bot_module.py

import discord
from discord.ext import commands
from dotenv import load_dotenv

from app.discord.application_process import setup as application_process_setup

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)
load_dotenv()

application_process_setup(bot)


@bot.event
async def on_ready():
    from app.discord.application_process.views import (
        AcceptOrCancelView,
        InterviewResultView,
    )

    bot.add_view(AcceptOrCancelView())
    bot.add_view(InterviewResultView())
    print(f"Logged in as {bot.user}")


def get_bot():
    return bot


#
# async def import_data():
#     import pandas as pd
#     import hashlib
#     from app.utils.encryption import aes_encrypt as encrypt
#
#     file_path = 'data.csv'
#     df = pd.read_csv(file_path)
#
#     def generate_email_hash(email: str) -> str:
#         return hashlib.sha256(email.encode('utf-8')).hexdigest()
#
#     for index, row in df.iterrows():
#         form_response = FormResponse(
#             name=row['你的名字?'],
#             email=row['電子郵件~'],
#             phone_number=str(row['電話號碼~~']),
#             high_school_stage=row['高中階段~~'],
#             city=row['你住在哪~~~'],
#             interested_fields=row['來找找適合你的領域~'].split(','),
#             preferred_order=str(row['排一排，告訴我們你的優先選擇吧！✨']),
#             reason_for_choice=row['為什麼選擇這些組別？🎯'],
#             related_experience=row['有什麼相關經驗或技能嗎？💡'],
#             email_hash=generate_email_hash(row['電子郵件~']),
#         )
#
#         form_response.save()
#
#         await send_initial_embed(form_response)
#
#         send_email(
#             subject="Counterspell / 已收到您的工作人員報名表！",
#             recipient=row['電子郵件~'],
#             template='emails/notification_email.html',
#             name=row['你的名字?'],
#             uuid=form_response.uuid
#         )
#
#     print("資料匯入完成！")

