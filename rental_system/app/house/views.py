from flask import render_template, redirect, url_for, flash, request, jsonify
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

@bp.route('/create', methods=['GET'])
@login_required
def create():
    return render_template('house/create.html')

@bp.route('/store', methods=['POST'])
@login_required
def store():
    try:
        house = House(
            landlord_id=current_user.id,
            title=request.form.get('title'),
            address=request.form.get('address'),
            district=request.form.get('district', ''),
            area=request.form.get('area', ''),
            type=request.form.get('type', ''),
            room_count=request.form.get('room_count', ''),
            size=float(request.form.get('size', 0)) if request.form.get('size') else None,
            rent_price=float(request.form.get('rent_price')),
            deposit=float(request.form.get('deposit', 0)) if request.form.get('deposit') else 0,
            decoration=request.form.get('decoration', ''),
            description=request.form.get('description', ''),
            province_code=request.form.get('province_code', ''),
            city_code=request.form.get('city_code', ''),
            district_code=request.form.get('district_code', '')
        )
        db.session.add(house)
        db.session.commit()
        flash('房源发布成功！', 'success')
        return redirect(url_for('house.detail', id=house.id))
    except Exception as e:
        db.session.rollback()
        flash(f'发布失败：{str(e)}', 'danger')
        return redirect(url_for('house.create'))
