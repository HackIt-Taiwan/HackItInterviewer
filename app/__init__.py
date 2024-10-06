# app/__init__.py
import os

from flask import Flask

from dotenv import load_dotenv
from mongoengine import connect

app = Flask(__name__)

def create_app():
    global app
    load_dotenv()

    # App configuration
    app.config['DEBUG'] = os.getenv('DEBUG') == 'True'

    # Here to load blueprint
    from app.routes.webhook import webhook_bp

    # Here to initialize the app
    connect(host=os.getenv('MONGO_URI'))

    # Here to register blueprint
    app.register_blueprint(webhook_bp)

    return app
