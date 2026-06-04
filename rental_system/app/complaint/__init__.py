from flask import Blueprint

bp = Blueprint('complaint', __name__)

from app.complaint import views
