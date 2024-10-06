# app/discord/import_existing_members/__init__.py
def setup(bot):
    """Initialize the import_existing_members module."""
    from .commands import setup as commands_setup

    commands_setup(bot)
