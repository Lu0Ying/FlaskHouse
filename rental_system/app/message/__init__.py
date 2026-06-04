from flask import Blueprint
bp = Blueprint('message', __name__)
from app.message import views
from app.message.views import send_message
