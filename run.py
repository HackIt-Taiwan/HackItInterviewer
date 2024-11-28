# app.py
import threading
from app.discord.bot_module import bot
from app import create_app
import os

app = create_app()


def run_discord_bot():
    bot.run(os.getenv('DISCORD_TOKEN'))


if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_discord_bot)
    bot_thread.start()

    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 80))
    app.run(debug=app.config['DEBUG'], host=host, port=port)
