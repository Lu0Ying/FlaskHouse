from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.stats import bp
from app.models import *

@bp.route('/')
def index():
    return render_template('stats/index.html')
