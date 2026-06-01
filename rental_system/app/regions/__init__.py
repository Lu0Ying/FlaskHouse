from flask import Blueprint, jsonify, request
from app import db
from app.models import Region

bp = Blueprint('regions', __name__, url_prefix='/api/regions')

@bp.route('/provinces', methods=['GET'])
def get_provinces():
    provinces = Region.get_provinces()
    return jsonify([{
        'code': p.code,
        'name': p.name
    } for p in provinces])

@bp.route('/<province_code>/cities', methods=['GET'])
def get_cities(province_code):
    cities = Region.get_cities(province_code)
    return jsonify([{
        'code': c.code,
        'name': c.name
    } for c in cities])

@bp.route('/<city_code>/districts', methods=['GET'])
def get_districts(city_code):
    districts = Region.get_districts(city_code)
    return jsonify([{
        'code': d.code,
        'name': d.name
    } for d in districts])

@bp.route('/search', methods=['GET'])
def search_regions():
    keyword = request.args.get('keyword', '')
    if not keyword or len(keyword) < 2:
        return jsonify([])
    
    regions = Region.search_by_name(keyword)[:20]
    return jsonify([{
        'code': r.code,
        'name': r.name,
        'level': r.level,
        'level_name': ['省', '市', '区'][r.level - 1] if r.level <= 3 else ''
    } for r in regions])

@bp.route('/validate', methods=['POST'])
def validate_region():
    data = request.get_json()
    code = data.get('code')
    name = data.get('name')
    level = data.get('level')
    
    if code:
        region = Region.get_by_code(code)
        if region:
            return jsonify({
                'valid': True,
                'region': {
                    'code': region.code,
                    'name': region.name,
                    'level': region.level
                }
            })
    
    if name:
        query = Region.query.filter(Region.name.like(f'%{name}%'), Region.is_active == True)
        if level:
            query = query.filter_by(level=level)
        region = query.first()
        if region:
            return jsonify({
                'valid': True,
                'region': {
                    'code': region.code,
                    'name': region.name,
                    'level': region.level
                }
            })
    
    return jsonify({'valid': False})