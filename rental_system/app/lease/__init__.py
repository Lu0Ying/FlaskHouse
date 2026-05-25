from flask import Blueprint
bp = Blueprint('lease', __name__)
from app.lease import views
