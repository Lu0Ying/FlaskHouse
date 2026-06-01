from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_, and_, func
from app import db
from app.search import bp
from app.models import House, Region


@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 12

    keyword = request.args.get('keyword', '').strip()
    province = request.args.get('province', '')
    city = request.args.get('city', '')
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
                House.description.contains(keyword),
                House.area.contains(keyword)
            )
        )

    if district:
        district_region = Region.query.filter_by(code=district).first()
        if district_region:
            query = query.filter(House.district == district_region.name)

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

    districts = db.session.query(House.district, func.count(House.id).label('count')).filter(
        House.status == 'available',
        House.district != ''
    ).group_by(House.district).all()

    room_counts = db.session.query(House.room_count, func.count(House.id).label('count')).filter(
        House.status == 'available',
        House.room_count != ''
    ).group_by(House.room_count).all()

    house_types = db.session.query(House.type, func.count(House.id).label('count')).filter(
        House.status == 'available',
        House.type != ''
    ).group_by(House.type).all()

    decorations = db.session.query(House.decoration, func.count(House.id).label('count')).filter(
        House.status == 'available',
        House.decoration != ''
    ).group_by(House.decoration).all()

    return render_template('search/index.html',
                          houses=houses,
                          districts=districts,
                          room_counts=room_counts,
                          house_types=house_types,
                          decorations=decorations,
                          keyword=keyword,
                          province=province,
                          city=city,
                          district=district,
                          house_type=house_type,
                          min_price=min_price,
                          max_price=max_price,
                          min_size=min_size,
                          max_size=max_size,
                          room_count=room_count,
                          decoration=decoration,
                          sort_by=sort_by)


@bp.route('/search', methods=['GET', 'POST'])
def search():
    page = request.args.get('page', 1, type=int)
    per_page = 12

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
                House.description.contains(keyword),
                House.area.contains(keyword)
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

    districts = db.session.query(House.district, func.count(House.id).label('count')).filter(
        House.status == 'available',
        House.district != ''
    ).group_by(House.district).all()

    room_counts = db.session.query(House.room_count, func.count(House.id).label('count')).filter(
        House.status == 'available',
        House.room_count != ''
    ).group_by(House.room_count).all()

    return render_template('search/search.html',
                          houses=houses,
                          districts=districts,
                          room_counts=room_counts,
                          keyword=keyword,
                          district=district,
                          house_type=house_type,
                          min_price=min_price,
                          max_price=max_price,
                          min_size=min_size,
                          max_size=max_size,
                          room_count=room_count,
                          decoration=decoration,
                          sort_by=sort_by)


@bp.route('/by-district', methods=['GET'])
def by_district():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    district = request.args.get('district', '').strip()

    if not district:
        flash('请选择区域', 'warning')
        return redirect(url_for('search.search'))

    houses = House.query.filter_by(status='available', district=district).order_by(
        House.created_at.desc()).paginate(page=page, per_page=per_page)

    total_count = House.query.filter_by(status='available', district=district).count()

    region = Region.query.filter_by(name=district, level=3).first()

    return render_template('search/by_district.html',
                          houses=houses,
                          district=district,
                          total_count=total_count,
                          region=region)


@bp.route('/by-room-count', methods=['GET'])
def by_room_count():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    room_count = request.args.get('room_count', '').strip()

    if not room_count:
        flash('请选择户型', 'warning')
        return redirect(url_for('search.search'))

    query = House.query.filter_by(status='available')

    if room_count == '4室及以上':
        query = query.filter(House.room_count.like('4室%'))
    else:
        query = query.filter(House.room_count == room_count)

    houses = query.order_by(House.created_at.desc()).paginate(page=page, per_page=per_page)

    total_count = query.count()

    return render_template('search/by_room_count.html',
                          houses=houses,
                          room_count=room_count,
                          total_count=total_count)


@bp.route('/recommendations')
def recommendations():
    page = request.args.get('page', 1, type=int)
    per_page = 12

    query = House.query.filter_by(status='available')

    if current_user.is_authenticated and current_user.is_landlord():
        query = query.filter(House.landlord_id != current_user.id)

    houses = query.order_by(House.created_at.desc()).paginate(page=page, per_page=per_page)

    return render_template('search/recommendations.html', houses=houses, is_recommendation=True)


@bp.route('/api/districts')
def api_districts():
    districts = db.session.query(
        House.district,
        func.count(House.id).label('count')
    ).filter(
        House.status == 'available',
        House.district != ''
    ).group_by(House.district).all()

    return jsonify({
        'districts': [{'name': d[0], 'count': d[1]} for d in districts]
    })


@bp.route('/api/room-counts')
def api_room_counts():
    room_counts = db.session.query(
        House.room_count,
        func.count(House.id).label('count')
    ).filter(
        House.status == 'available',
        House.room_count != ''
    ).group_by(House.room_count).all()

    return jsonify({
        'room_counts': [{'name': r[0], 'count': r[1]} for r in room_counts]
    })


@bp.route('/api/house/<int:id>')
def api_house(id):
    house = House.query.get(id)
    if not house:
        return jsonify({'error': 'House not found'}), 404

    images = [img.url for img in house.get_images()]

    return jsonify({
        'id': house.id,
        'title': house.title,
        'address': house.address,
        'district': house.district,
        'area': house.area,
        'type': house.type,
        'room_count': house.room_count,
        'size': house.size,
        'rent_price': house.rent_price,
        'deposit': house.deposit,
        'decoration': house.decoration,
        'description': house.description,
        'images': images,
        'landlord': {
            'id': house.landlord.id,
            'username': house.landlord.username
        }
    })


@bp.route('/quick-search')
def quick_search():
    keyword = request.args.get('keyword', '').strip()

    if len(keyword) < 1:
        return jsonify({'results': []})

    houses = House.query.filter(
        House.status == 'available',
        or_(
            House.title.contains(keyword),
            House.address.contains(keyword),
            House.district.contains(keyword)
        )
    ).limit(10).all()

    results = [{
        'id': h.id,
        'title': h.title,
        'address': h.address,
        'rent_price': h.rent_price,
        'room_count': h.room_count
    } for h in houses]

    return jsonify({'results': results})
