from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import or_, and_, func
from app import db
from app.search import bp
from app.models import *

@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 6
    
    keyword = request.args.get('keyword', '').strip()
    district = request.args.get('district', '')
    house_type = request.args.get('house_type', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    min_size = request.args.get('min_size', type=float)
    max_size = request.args.get('max_size', type=float)
    room_count = request.args.get('room_count', '')
    decoration = request.args.get('decoration', '')
    sort_by = request.args.get('sort_by', 'created_at')
    
    query = House.query.filter_by(status='available')
    
    if keyword:
        query = query.filter(
            or_(
                House.title.contains(keyword),
                House.address.contains(keyword),
                House.district.contains(keyword),
                House.description.contains(keyword)
            )
        )
    
    if district:
        query = query.filter(House.district == district)
    
    if house_type:
        query = query.filter(House.type == house_type)
    
    if min_price is not None:
        query = query.filter(House.rent_price >= min_price)
    
    if max_price is not None:
        query = query.filter(House.rent_price <= max_price)
    
    if min_size is not None:
        query = query.filter(House.size >= min_size)
    
    if max_size is not None:
        query = query.filter(House.size <= max_size)
    
    if room_count:
        if room_count == '4室及以上':
            query = query.filter(House.room_count.like('4室%'))
        else:
            query = query.filter(House.room_count == room_count)
    
    if decoration:
        query = query.filter(House.decoration == decoration)
    
    if sort_by == 'rent_price':
        query = query.order_by(House.rent_price.asc())
    elif sort_by == 'rent_price_desc':
        query = query.order_by(House.rent_price.desc())
    elif sort_by == 'size':
        query = query.order_by(House.size.desc())
    else:
        query = query.order_by(House.created_at.desc())
    
    houses = query.paginate(page=page, per_page=per_page)
    
    return render_template('search/index.html', houses=houses)

@bp.route('/recommendations')
@login_required
def recommendations():
    page = request.args.get('page', 1, type=int)
    per_page = 6
    
    query = House.query.filter_by(status='available')
    
    if current_user.is_authenticated:
        if current_user.is_landlord():
            query = query.filter(House.landlord_id != current_user.id)
    
    houses = query.order_by(House.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('search/index.html', houses=houses, is_recommendation=True)
