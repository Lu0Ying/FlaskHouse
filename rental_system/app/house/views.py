from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.house import bp
from app.models import *
from app.utils import log_action
from app.utils.file_upload import save_upload_file, delete_file, allowed_file
from app.utils.file_upload import init_chunk_upload, save_chunk, merge_chunks, cleanup_chunks
import json

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
    all_media = HouseMedia.query.filter_by(house_id=house.id).order_by(HouseMedia.order).all()
    images = [m for m in all_media if m.media_type == 'image']
    videos = [m for m in all_media if m.media_type == 'video']
    return render_template('house/detail.html', house=house, images=images, videos=videos)

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
        log_action('创建房源', user_id=current_user.id, details={'house_id': house.id, 'title': house.title})

        # 关联已上传的媒体文件
        media_paths = request.form.get('media_paths', '[]')
        try:
            paths = json.loads(media_paths)
            for idx, path in enumerate(paths):
                ext = path.rsplit('.', 1)[-1].lower() if '.' in path else ''
                media_type = 'video' if ext == 'mp4' else 'image'
                media = HouseMedia(
                    house_id=house.id,
                    media_type=media_type,
                    url=path,
                    order=idx
                )
                db.session.add(media)
            if paths:
                db.session.commit()
        except (json.JSONDecodeError, Exception):
            pass

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
        log_action('删除房源', user_id=current_user.id, details={'house_id': house.id, 'title': house.title})
        db.session.delete(house)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# ==================== 分块上传接口 ====================

@bp.route('/ajax/chunk/init', methods=['POST'])
@login_required
def chunk_upload_init():
    """初始化分块上传"""
    data = request.get_json(silent=True) or {}
    filename = data.get('filename', '')
    if not filename:
        return jsonify({'success': False, 'message': '缺少文件名'})
    
    if not allowed_file(filename):
        return jsonify({'success': False, 'message': '不支持的文件类型'})
    
    upload_id = init_chunk_upload(filename)
    return jsonify({'success': True, 'upload_id': upload_id})


@bp.route('/ajax/chunk/upload', methods=['POST'])
@login_required
def chunk_upload_part():
    """上传单个分块"""
    upload_id = request.form.get('upload_id', '')
    chunk_index = request.form.get('chunk_index', '')
    
    if not upload_id or chunk_index == '':
        return jsonify({'success': False, 'message': '缺少参数'})
    
    chunk_file = request.files.get('chunk')
    if not chunk_file:
        return jsonify({'success': False, 'message': '没有分块数据'})
    
    chunk_data = chunk_file.read()
    
    if save_chunk(upload_id, int(chunk_index), chunk_data):
        return jsonify({'success': True, 'chunk_index': int(chunk_index)})
    else:
        return jsonify({'success': False, 'message': '保存分块失败'})


@bp.route('/ajax/chunk/merge', methods=['POST'])
@login_required
def chunk_upload_merge():
    """合并分块"""
    data = request.get_json(silent=True) or {}
    upload_id = data.get('upload_id', '')
    if not upload_id:
        return jsonify({'success': False, 'message': '缺少 upload_id'})
    
    filepath = merge_chunks(upload_id, subfolder='uploads')
    if not filepath:
        return jsonify({'success': False, 'message': '合并失败，可能分块不完整'})
    
    return jsonify({'success': True, 'url': filepath})


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
            log_action('更新房源', user_id=current_user.id, details={'house_id': house.id, 'title': house.title})
            flash('房源更新成功！', 'success')
            return redirect(url_for('user.house_detail', id=house.id))
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败：{str(e)}', 'danger')
    
    return render_template('house/edit.html', house=house)


@bp.route('/<int:id>/media_list')
@login_required
def get_media_list(id):
    """获取房源的媒体列表（供 AJAX 加载）"""
    house = House.query.get_or_404(id)
    if house.landlord_id != current_user.id and not current_user.is_admin():
        return jsonify([])
    
    media_list = HouseMedia.query.filter_by(house_id=house.id).order_by(HouseMedia.order).all()
    return jsonify([{
        'id': m.id,
        'type': m.media_type,
        'url': m.url,
        'order': m.order
    } for m in media_list])


@bp.route('/temp-upload', methods=['POST'])
@login_required
def temp_upload():
    """临时上传文件（发布页面用，house 尚未创建）"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有上传文件'})
    
    file = request.files['file']
    if not file.filename:
        return jsonify({'success': False, 'message': '文件名为空'})
    
    filepath = save_upload_file(file, subfolder='uploads')
    if not filepath:
        return jsonify({'success': False, 'message': '文件类型不允许或保存失败'})
    
    return jsonify({'success': True, 'url': filepath})


@bp.route('/temp-delete', methods=['POST'])
@login_required
def temp_delete():
    """删除临时上传的文件"""
    data = request.get_json(silent=True) or {}
    filepath = data.get('url', '')
    if filepath:
        delete_file(filepath)
    return jsonify({'success': True})


@bp.route('/<int:id>/media/upload', methods=['POST'])
@login_required
def upload_media(id):
    """上传媒体文件并关联到已有房源（编辑页面用）"""
    house = House.query.get_or_404(id)
    if house.landlord_id != current_user.id and not current_user.is_admin():
        return jsonify({'success': False, 'message': '无权操作'})
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有上传文件'})
    
    file = request.files['file']
    if not file.filename:
        return jsonify({'success': False, 'message': '文件名为空'})
    
    filepath = save_upload_file(file, subfolder='uploads')
    if not filepath:
        return jsonify({'success': False, 'message': '文件类型不允许或保存失败'})
    
    ext = filepath.rsplit('.', 1)[-1].lower() if '.' in filepath else ''
    media_type = 'video' if ext == 'mp4' else 'image'
    
    # 计算当前最大排序值
    max_order = db.session.query(db.func.max(HouseMedia.order)).filter(
        HouseMedia.house_id == house.id).scalar() or -1
    
    media = HouseMedia(
        house_id=house.id,
        media_type=media_type,
        url=filepath,
        order=max_order + 1
    )
    db.session.add(media)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'media_id': media.id,
        'url': media.url,
        'type': media.media_type,
        'order': media.order
    })


@bp.route('/<int:id>/media/upload-by-path', methods=['POST'])
@login_required
def upload_media_by_path(id):
    """将已上传的文件路径关联到房源（分块合并后使用）"""
    house = House.query.get_or_404(id)
    if house.landlord_id != current_user.id and not current_user.is_admin():
        return jsonify({'success': False, 'message': '无权操作'})

    data = request.get_json(silent=True) or {}
    filepath = data.get('url', '')
    if not filepath:
        return jsonify({'success': False, 'message': '缺少文件路径'})

    ext = filepath.rsplit('.', 1)[-1].lower() if '.' in filepath else ''
    media_type = 'video' if ext == 'mp4' else 'image'

    max_order = db.session.query(db.func.max(HouseMedia.order)).filter(
        HouseMedia.house_id == house.id).scalar() or -1

    media = HouseMedia(
        house_id=house.id,
        media_type=media_type,
        url=filepath,
        order=max_order + 1
    )
    db.session.add(media)
    db.session.commit()

    return jsonify({
        'success': True,
        'media_id': media.id,
        'url': media.url,
        'type': media.media_type,
        'order': media.order
    })


@bp.route('/<int:id>/media/delete', methods=['POST'])
@login_required
def delete_media(id):
    """删除房源媒体文件"""
    house = House.query.get_or_404(id)
    if house.landlord_id != current_user.id and not current_user.is_admin():
        return jsonify({'success': False, 'message': '无权操作'})
    
    data = request.get_json(silent=True) or {}
    media_id = data.get('media_id')
    if not media_id:
        return jsonify({'success': False, 'message': '缺少 media_id'})
    
    media = HouseMedia.query.get_or_404(media_id)
    if media.house_id != house.id:
        return jsonify({'success': False, 'message': '媒体不属于该房源'})
    
    # 删除物理文件
    delete_file(media.url)
    # 删除数据库记录
    db.session.delete(media)
    db.session.commit()
    
    return jsonify({'success': True})
