from flask import Blueprint
bp = Blueprint('monitor', __name__)
from app.monitor import views
