# app/discord/bot_module.py
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from app.discord.import_existing_members import setup as import_existing_members_setup

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)
load_dotenv()

import_existing_members_setup(bot)
