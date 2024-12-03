# app/discord/customs/__init__.py
def setup(bot):
    """Initialize the customs module."""
    from .commands import setup as commands_setup

    commands_setup(bot)