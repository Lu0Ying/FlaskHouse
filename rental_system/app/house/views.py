from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.house import bp
from app.models import *

@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    houses = House.query.order_by(House.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('house/index.html', houses=houses)

@bp.route('/<int:id>')
def detail(id):
    house = House.query.get_or_404(id)
    return render_template('house/detail.html', house=house)
