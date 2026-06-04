from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.house import bp
from app.models import *

@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    # 只显示状态为可租的房源
    query = House.query.filter_by(status='available').order_by(House.created_at.desc())
    
    # 用户未登录时只显示前6个房源，登录后显示全部（分页）
    if current_user.is_authenticated:
        houses = query.paginate(page=page, per_page=10)
    else:
        # 未登录时只取前6条，不分页
        houses = query.limit(6).all()
    
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


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """删除房源（API接口）"""
    house = House.query.get_or_404(id)
    
    # 验证权限：只有房东本人或管理员可以删除
    if house.landlord_id != current_user.id and not current_user.is_admin():
        return jsonify({'success': False, 'message': '您无权删除此房源'})
    
    try:
        db.session.delete(house)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """编辑房源"""
    house = House.query.get_or_404(id)
    
    # 验证权限：只有房东本人可以编辑
    if house.landlord_id != current_user.id:
        flash('您无权编辑此房源', 'danger')
        return redirect(url_for('house.index'))
    
    if request.method == 'POST':
        try:
            house.title = request.form.get('title')
            house.address = request.form.get('address')
            house.district = request.form.get('district', '')
            house.area = request.form.get('area', '')
            house.type = request.form.get('type', '')
            house.room_count = request.form.get('room_count', '')
            house.size = float(request.form.get('size', 0)) if request.form.get('size') else None
            house.rent_price = float(request.form.get('rent_price'))
            house.deposit = float(request.form.get('deposit', 0)) if request.form.get('deposit') else 0
            house.decoration = request.form.get('decoration', '')
            house.description = request.form.get('description', '')
            
            # 处理房源状态修改限制
            new_status = request.form.get('status', house.status)
            
            # 如果当前状态是"已租"，不允许修改状态
            if house.status == 'rented':
                # 保持原状态不变
                pass  # house.status 保持不变
            else:
                # 如果当前状态不是"已租"，只允许在"可租"和"维修中"之间切换
                if new_status in ['available', 'maintenance']:
                    house.status = new_status
                else:
                    # 如果尝试设置为其他状态，保持原状态不变
                    pass
            
            house.province_code = request.form.get('province_code', '')
            house.city_code = request.form.get('city_code', '')
            house.district_code = request.form.get('district_code', '')
            
            db.session.commit()
            flash('房源更新成功！', 'success')
            return redirect(url_for('user.house_detail', id=house.id))
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败：{str(e)}', 'danger')
    
    return render_template('house/edit.html', house=house)
