# app.py
from gevent import monkey

monkey.patch_all()  # This allows Gevent to monkey-patch standard libraries for non-blocking IO

import gevent
import os
from application.discord.bot_module import bot
from app import create_app

app = create_app()


def start_flask():
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 80))
    app.run(
        debug=app.config["DEBUG"],
        host=host,
        port=port,
        threaded=True,
        use_reloader=False,
    )


def start_discord_bot():
    bot.run(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    # Start Flask in a gevent greenlet
    flask_greenlet = gevent.spawn(start_flask)

    # Start the Discord bot in a separate greenlet
    discord_greenlet = gevent.spawn(start_discord_bot)

    # Wait for both tasks to finish
    gevent.joinall([flask_greenlet, discord_greenlet])
