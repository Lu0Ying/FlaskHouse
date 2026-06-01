from flask import Blueprint

bp = Blueprint('complaint', __name__, url_prefix='/complaint')

from app.complaint import views
