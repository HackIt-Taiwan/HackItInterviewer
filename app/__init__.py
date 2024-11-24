# app/__init__.py
import os

from flask import Flask

from dotenv import load_dotenv
from flask_mailman import Mail

app = Flask(__name__)
mail = Mail()


def create_app():
    global app
    load_dotenv()

    # App configuration
    app.config["DEBUG"] = os.getenv("DEBUG") == "True"

    # Mail configuration
    # app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    # app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 465))
    # app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'false').lower() in ['true', 'on', '1']
    # app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'true').lower() in ['true', 'on', '1']
    # app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    # app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    # app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

    # Here to load blueprint
    from app.routes.redirect import redirect_bp
    from app.routes.application import application_bp
    from app.routes.email_preview import email_preview_bp

    # Here to initialize the app
    # mail.init_app(app)

    # Here to register blueprint
    app.register_blueprint(email_preview_bp, url_prefix="/admin/preview")
    app.register_blueprint(application_bp, url_prefix="/apply")
    app.register_blueprint(redirect_bp, url_prefix="/redirect")

    return app
