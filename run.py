# app.py
import threading
from app.discord.bot_module import bot
from app import create_app
import os

app = create_app()


def run_discord_bot():
    bot.run(os.getenv("DISCORD_TOKEN"))


# Bad idea, should've used quart or something much more elegant.
if __name__ == "__main__":
    # if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        # bot_thread = threading.Thread(target=run_discord_bot)
        # bot_thread.start()

    # Use the code above if your bot ran twice.
    bot_thread = threading.Thread(target=run_discord_bot)
    bot_thread.start()

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 80))
    app.run(debug=app.config["DEBUG"],  host=host, port=port)
