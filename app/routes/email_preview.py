# app/routes/email_preview.py
from flask import Blueprint, render_template, request

email_preview_bp = Blueprint('email_preview', __name__)


@email_preview_bp.route('/email')
def preview():
    # get ?email_template=...&name=...&uuid=...&reason=...
    email_template = request.args.get('email_template')
    name = request.args.get('name')
    uuid = request.args.get('uuid')
    email = request.args.get('email')
    reason = request.args.get('reason', '').replace('|', '<br>')
    return render_template(email_template, name=name, uuid=uuid, reason=reason, email=email)


@email_preview_bp.route('/')
def testing():
    return "itworks"
