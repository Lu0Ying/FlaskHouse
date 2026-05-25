from flask import Blueprint
bp = Blueprint('repair', __name__)
from app.repair import views
