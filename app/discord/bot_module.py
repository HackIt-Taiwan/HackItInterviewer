# app/discord/bot_module.py
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from app.discord.import_existing_members import setup as import_existing_members_setup
from app.discord.application_process import setup as application_process_setup

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)
load_dotenv()

import_existing_members_setup(bot)
application_process_setup(bot)

# Make the bot instance accessible globally
def get_bot():
    return bot
