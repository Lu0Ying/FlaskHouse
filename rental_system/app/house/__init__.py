from flask import Blueprint

bp = Blueprint('house', __name__)

from app.house import views
