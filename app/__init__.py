# app/__init__.py
import os

from flask import Flask, render_template

from dotenv import load_dotenv
from flask_mailman import EmailMessage, Mail

app = Flask(__name__)
mail = Mail()


def create_app():
    global app
    load_dotenv()

    # App configuration
    app.config["DEBUG"] = os.getenv("DEBUG") == "True"

    # Mail configuration
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 465))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'false').lower() in ['true', 'on', '1']
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'true').lower() in ['true', 'on', '1']
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

    print(app.config['MAIL_SERVER'])
    print(app.config['MAIL_PORT'])
    print(app.config['MAIL_USE_TLS'])
    print(app.config['MAIL_USE_SSL'])
    print(app.config['MAIL_USERNAME'])
    print(app.config['MAIL_PASSWORD'])
    print(app.config['MAIL_DEFAULT_SENDER'])

    mail.init_app(app)

    try:
        msg = EmailMessage(
            subject="Test Email from Flask App",
            body="This is a test email sent during app initialization.",
            from_email=app.config['MAIL_DEFAULT_SENDER'],
            to=["jebijiw696@owube.com"]  # Sending to the same email for test purposes
        )
        msg.send()
        print("Test email sent successfully!")
    except Exception as e:
        print(f"Failed to send test email: {e}")
        
    # Here to load blueprint
    from app.routes.application import application_bp
    from app.routes.email_preview import email_preview_bp

    # Here to register blueprint
    app.register_blueprint(email_preview_bp, url_prefix="/admin/preview")
    app.register_blueprint(application_bp, url_prefix="/apply")

    # Don't mind about this
    @app.errorhandler(404)
    def page_not_found(e):
        #snip
        return render_template('404.html'), 404

    return app
