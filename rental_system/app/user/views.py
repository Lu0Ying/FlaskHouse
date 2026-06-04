from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.user import bp
from app.models import User, House, LeaseContract, Appointment, RepairRequest, Message
from app.utils import log_action
from app.models import User, House, LeaseContract, Appointment, RepairRequest, Message, HouseMedia


@bp.route('/')
@login_required
def index():
    return redirect(url_for('user.profile'))


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        action = request.form.get('action', 'info')

        if action == 'info':
            current_user.real_name = request.form.get('real_name', '').strip()
            current_user.phone = request.form.get('phone', '').strip()
            current_user.id_card = request.form.get('id_card', '').strip()
            db.session.commit()
            log_action('更新个人信息', user_id=current_user.id, details={'username': current_user.username})
            flash('个人信息已更新', 'success')

        elif action == 'password':
            old_password = request.form.get('old_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')

            if not current_user.check_password(old_password):
                flash('原密码错误', 'danger')
                return redirect(url_for('user.profile'))

            if len(new_password) < 6:
                flash('新密码长度至少6位', 'danger')
                return redirect(url_for('user.profile'))

            if new_password != confirm_password:
                flash('两次输入的密码不一致', 'danger')
                return redirect(url_for('user.profile'))

            current_user.set_password(new_password)
            db.session.commit()
            log_action('修改密码', user_id=current_user.id, details={'username': current_user.username})
            flash('密码已修改', 'success')

    return render_template('user/profile.html', user=current_user)


@bp.route('/avatar', methods=['POST'])
@login_required
def avatar():
    if 'avatar' not in request.files:
        flash('请选择要上传的图片', 'danger')
        return redirect(url_for('user.profile'))

    file = request.files['avatar']
    if file.filename == '':
        flash('请选择要上传的图片', 'danger')
        return redirect(url_for('user.profile'))

    from app.utils.file_upload import save_upload_file
    filepath = save_upload_file(file, subfolder='avatars')

    if filepath:
        current_user.avatar = filepath
        db.session.commit()
        flash('头像已更新', 'success')
    else:
        flash('上传失败，请检查文件格式', 'danger')

    return redirect(url_for('user.profile'))


@bp.route('/my-houses')
@login_required
def my_houses():
    if not current_user.is_landlord():
        flash('只有房东可以管理房源', 'danger')
        return redirect(url_for('house.index'))

    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')

    query = House.query.filter_by(landlord_id=current_user.id)

    if status:
        query = query.filter_by(status=status)

    houses = query.order_by(House.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('user/my_houses.html', houses=houses, status=status)


@bp.route('/house/<int:id>')
@login_required
def house_detail(id):
    """房东专属的房源详情页"""
    if not current_user.is_landlord():
        flash('只有房东可以查看此页面', 'danger')
        return redirect(url_for('house.index'))
    
    house = House.query.get_or_404(id)
    
    # 验证是否为该房东的房源
    if house.landlord_id != current_user.id:
        flash('您无权查看此房源', 'danger')
        return redirect(url_for('user.my_houses'))
    
    # 获取统计信息（可选）
    view_count = 0  # TODO: 实现浏览计数功能
    appointment_count = house.appointments.count()
    contract_count = house.contracts.count()
    repair_count = house.repair_requests.count()
    
    return render_template('user/landlord_house_detail.html', 
                          house=house,
                          images=[m for m in HouseMedia.query.filter_by(house_id=house.id, media_type='image').order_by(HouseMedia.order).all()],
                          videos=[m for m in HouseMedia.query.filter_by(house_id=house.id, media_type='video').order_by(HouseMedia.order).all()],
                          view_count=view_count,
                          appointment_count=appointment_count,
                          contract_count=contract_count,
                          repair_count=repair_count)


@bp.route('/my-appointments')
@login_required
def my_appointments():
    if current_user.is_tenant():
        return redirect(url_for('lease.my_appointments'))
    elif current_user.is_landlord():
        return redirect(url_for('lease.landlord_appointments'))
    flash('无权访问', 'danger')
    return redirect(url_for('house.index'))


@bp.route('/my-contracts')
@login_required
def my_contracts():
    return redirect(url_for('lease.contracts'))


@bp.route('/my-messages')
@login_required
def my_messages():
    return redirect(url_for('message.inbox'))


@bp.route('/my-repairs')
@login_required
def my_repairs():
    if current_user.is_tenant():
        return redirect(url_for('repair.my_repairs'))
    elif current_user.is_landlord():
        return redirect(url_for('repair.landlord_repairs'))
    flash('无权访问', 'danger')
    return redirect(url_for('house.index'))


@bp.route('/my-complaints')
@login_required
def my_complaints():
    if current_user.is_tenant():
        return redirect(url_for('complaint.my_complaints'))
    flash('无权访问', 'danger')
    return redirect(url_for('house.index'))


@bp.route('/my-news')
@login_required
def my_news():
    if current_user.is_landlord() or current_user.is_admin():
        return redirect(url_for('news.my_news'))
    flash('无权访问', 'danger')
    return redirect(url_for('house.index'))


@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin():
        return redirect(url_for('stats.admin_dashboard'))
    elif current_user.is_landlord():
        return redirect(url_for('stats.landlord_dashboard'))
    else:
        return redirect(url_for('stats.tenant_dashboard'))


@bp.route('/view/<int:id>')
@login_required
def view(id):
    user = User.query.get_or_404(id)
    if current_user.id != user.id and not current_user.is_admin():
        flash('您无权查看此用户信息', 'danger')
        return redirect(url_for('user.profile'))
    if request.method == 'POST':
        # 只有管理员可以修改用户信息
        if not current_user.is_admin():
            flash('只有管理员可以修改用户信息', 'danger')
            return redirect(url_for('user.view', id=id))
        
        # 更新用户信息
        user.username = request.form.get('username', '').strip()
        user.email = request.form.get('email', '').strip()
        user.real_name = request.form.get('real_name', '').strip()
        user.phone = request.form.get('phone', '').strip()
        user.id_card = request.form.get('id_card', '').strip()
        user.role = request.form.get('role', 'tenant')
        user.status = request.form.get('status', 'active')
        
        db.session.commit()
        log_action('管理员编辑用户', user_id=current_user.id, details={'target_user_id': user.id, 'username': user.username, 'role': user.role, 'status': user.status})
        flash('用户信息已更新', 'success')
        return redirect(url_for('user.view', id=id))
    
    return render_template('user/view.html', user=user)
