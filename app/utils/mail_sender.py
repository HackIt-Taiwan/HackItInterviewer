# app/utils/mail_sender.py
import threading
from flask import render_template
from flask_mailman import EmailMessage

def send_async_email(app, msg):
    with app.app_context():
        msg.send()

def send_email(subject, recipient, template, **kwargs):
    from app import app
    with app.app_context():
        msg = EmailMessage(
            subject=subject,
            body=render_template(template, **kwargs),
            from_email=app.config["MAIL_DEFAULT_SENDER"],
            to=[recipient]
        )
        msg.content_subtype = 'html'
        thread = threading.Thread(target=send_async_email, args=(app, msg))
        thread.start()
