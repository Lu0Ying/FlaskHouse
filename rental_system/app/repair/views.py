from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.repair import bp
from app.models import RepairRequest, House, LeaseContract, User


@bp.route('/')
@login_required
def index():
    if current_user.is_tenant():
        return redirect(url_for('repair.my_repairs'))
    elif current_user.is_landlord():
        return redirect(url_for('repair.landlord_repairs'))
    else:
        return redirect(url_for('repair.all_repairs'))


@bp.route('/my-repairs')
@login_required
def my_repairs():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')

    query = RepairRequest.query.filter_by(tenant_id=current_user.id)

    if status:
        query = query.filter_by(status=status)

    repairs = query.order_by(RepairRequest.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('repair/my_repairs.html', repairs=repairs)


@bp.route('/tenant-create', methods=['GET', 'POST'])
@login_required
def tenant_create():
    """租客发起维修申请"""
    # 获取租客的有效租赁合同
    active_contracts = LeaseContract.query.filter_by(
        tenant_id=current_user.id, status='active'
    ).all()
    
    # 过滤掉有待处理或处理中维修申请的房源
    # 允许发起新申请的条件：没有维修申请 或 只有已拒绝/已完成的记录
    filtered_contracts = []
    for contract in active_contracts:
        # 检查该房源是否有待处理或处理中的维修申请
        active_repair = RepairRequest.query.filter(
            RepairRequest.house_id == contract.house_id,
            RepairRequest.tenant_id == current_user.id,
            RepairRequest.status.in_(['pending', 'processing'])
        ).first()
        
        # 只有没有待处理或处理中维修申请的房源才加入列表
        if not active_repair:
            filtered_contracts.append(contract)
    
    # 获取每个合同关联的房源信息（确保加载）
    for contract in filtered_contracts:
        _ = contract.house
        _ = contract.landlord
    
    if request.method == 'POST':
        contract_id = request.form.get('contract_id', type=int)
        description = request.form.get('description', '').strip()
        media_paths = request.form.get('media_paths', '[]')
        
        if not contract_id:
            flash('请选择要维修的房源', 'danger')
            return redirect(url_for('repair.tenant_create'))
        
        if not description:
            flash('请填写维修描述', 'danger')
            return redirect(url_for('repair.tenant_create'))
        
        # 验证租赁合同
        contract = LeaseContract.query.filter_by(
            id=contract_id,
            tenant_id=current_user.id,
            status='active'
        ).first()
        
        if not contract:
            flash('无效的租赁合同', 'danger')
            return redirect(url_for('repair.tenant_create'))
        
        # 再次检查是否有待处理或处理中的维修申请（防止并发提交）
        active_repair = RepairRequest.query.filter(
            RepairRequest.house_id == contract.house_id,
            RepairRequest.tenant_id == current_user.id,
            RepairRequest.status.in_(['pending', 'processing'])
        ).first()
        
        if active_repair:
            flash('该房源有待处理或处理中的维修申请，不能重复提交', 'danger')
            return redirect(url_for('repair.tenant_create'))
        
        house_id = contract.house_id
        
        # 创建维修申请
        repair = RepairRequest(
            tenant_id=current_user.id,
            house_id=house_id,
            description=description,
            images=media_paths,
            status='pending'
        )
        db.session.add(repair)
        db.session.commit()
        
        flash('维修申请已提交，请等待处理', 'success')
        return redirect(url_for('repair.my_repairs'))
    
    return render_template('repair/tenant_create.html', active_contracts=filtered_contracts)


@bp.route('/landlord-repairs')
@login_required
def landlord_repairs():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')

    house_ids = [h.id for h in House.query.filter_by(landlord_id=current_user.id).all()]
    query = RepairRequest.query.filter(RepairRequest.house_id.in_(house_ids))

    if status:
        query = query.filter_by(status=status)

    repairs = query.order_by(RepairRequest.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('repair/landlord_repairs.html', repairs=repairs)


@bp.route('/all-repairs')
@login_required
def all_repairs():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')

    query = RepairRequest.query

    if status:
        query = query.filter_by(status=status)

    repairs = query.order_by(RepairRequest.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('repair/all_repairs.html', repairs=repairs)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        house_id = request.form.get('house_id', type=int)
        description = request.form.get('description', '').strip()
        images_json = request.form.get('images', '')

        if not house_id or not description:
            flash('请选择房源并填写维修描述', 'danger')
            return redirect(url_for('repair.create'))

        house = House.query.get(house_id)
        if not house:
            flash('房源不存在', 'danger')
            return redirect(url_for('repair.create'))

        if current_user.is_tenant():
            active_lease = LeaseContract.query.filter_by(
                house_id=house_id, tenant_id=current_user.id, status='active').first()
            if not active_lease:
                flash('您只能为您租住的房源提交维修申请', 'danger')
                return redirect(url_for('repair.create'))
        elif current_user.is_landlord():
            if house.landlord_id != current_user.id:
                flash('您只能为您自己的房源提交维修申请', 'danger')
                return redirect(url_for('repair.create'))

        repair = RepairRequest(
            tenant_id=current_user.id,
            house_id=house_id,
            description=description,
            images=images_json,
            status='pending'
        )
        db.session.add(repair)
        db.session.commit()

        flash('维修申请已提交，请等待处理', 'success')
        return redirect(url_for('repair.my_repairs'))

    houses = []
    if current_user.is_tenant():
        leases = LeaseContract.query.filter_by(tenant_id=current_user.id, status='active').all()
        houses = [lease.house for lease in leases]
    elif current_user.is_landlord():
        houses = House.query.filter_by(landlord_id=current_user.id).all()

    return render_template('repair/create.html', houses=houses)


@bp.route('/detail/<int:id>')
@login_required
def detail(id):
    repair = RepairRequest.query.get_or_404(id)

    if current_user.id == repair.tenant_id:
        pass
    elif current_user.is_landlord():
        house = House.query.get(repair.house_id)
        if house.landlord_id != current_user.id and not current_user.is_admin():
            flash('您无权查看此维修申请', 'danger')
            return redirect(url_for('repair.index'))
    elif not current_user.is_admin():
        flash('您无权查看此维修申请', 'danger')
        return redirect(url_for('repair.index'))

    return render_template('repair/detail.html', repair=repair)


@bp.route('/process/<int:id>', methods=['GET', 'POST'])
@login_required
def process(id):
    repair = RepairRequest.query.get_or_404(id)

    if current_user.is_landlord():
        house = House.query.get(repair.house_id)
        if house.landlord_id != current_user.id:
            flash('您无权处理此维修申请', 'danger')
            return redirect(url_for('repair.landlord_repairs'))
    elif not current_user.is_admin():
        flash('您无权处理此维修申请', 'danger')
        return redirect(url_for('repair.index'))

    if request.method == 'POST':
        action = request.form.get('action')
        house = House.query.get(repair.house_id)

        if action == 'accept':
            repair.status = 'processing'
            house.status = 'maintenance'
            flash('已接受维修申请，正在处理中', 'success')
        elif action == 'complete':
            repair.status = 'completed'
            repair.resolved_at = datetime.now()
            if house.status == 'maintenance':
                house.status = 'rented'
            flash('维修已完成', 'success')
        elif action == 'reject':
            repair.status = 'rejected'
            repair.resolved_at = datetime.now()
            if house.status == 'maintenance':
                house.status = 'rented'
            flash('已拒绝维修申请', 'success')

        db.session.commit()
        if current_user.is_admin():
            return redirect(url_for('repair.all_repairs'))
        else:
            return redirect(url_for('repair.landlord_repairs'))

    return render_template('repair/process.html', repair=repair)


@bp.route('/cancel/<int:id>', methods=['POST'])
@login_required
def cancel(id):
    repair = RepairRequest.query.get_or_404(id)

    if current_user.id != repair.tenant_id:
        flash('您无权取消此维修申请', 'danger')
        return redirect(url_for('repair.my_repairs'))

    if repair.status not in ['pending']:
        flash('当前状态不允许取消', 'danger')
        return redirect(url_for('repair.my_repairs'))

    repair.status = 'rejected'
    repair.resolved_at = datetime.now()
    db.session.commit()

    flash('已取消维修申请', 'success')
    return redirect(url_for('repair.my_repairs'))


@bp.route('/landlord-cancel/<int:id>', methods=['GET', 'POST'])
@login_required
def landlord_cancel(id):
    """房东申请取消维修申请，给管理员发消息"""
    from app.message import send_message
    
    repair = RepairRequest.query.get_or_404(id)
    
    if current_user.is_landlord():
        house = House.query.get(repair.house_id)
        if house.landlord_id != current_user.id:
            flash('您无权取消此维修申请', 'danger')
            return redirect(url_for('repair.landlord_repairs'))
    else:
        flash('您无权取消此维修申请', 'danger')
        return redirect(url_for('repair.index'))
    
    # 获取第一个管理员
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        flash('未找到管理员', 'danger')
        return redirect(url_for('repair.landlord_repairs'))
    
    if request.method == 'POST':
        reason = request.form.get('reason', '').strip()
        if not reason:
            flash('请填写取消原因', 'danger')
            return redirect(url_for('repair.landlord_cancel', id=id))
        
        # 构建消息内容
        message_content = """房东申请取消维修申请 #%d

房源信息：%s - %s
租客：%s
维修描述：%s
取消原因：%s

请管理员处理此取消申请。
        """.strip() % (
            repair.id,
            repair.house.title,
            repair.house.address,
            repair.tenant.username,
            repair.description,
            reason
        )
        
        # 发送消息给管理员
        send_message(current_user.id, admin.id, message_content)
        
        # 不立即拒绝，只发消息通知管理员
        flash('已发送取消申请消息给管理员，请等待管理员处理', 'success')
        return redirect(url_for('repair.landlord_repairs'))
    
    return render_template('repair/landlord_cancel.html', repair=repair, admin=admin)


@bp.route('/admin-cancel/<int:id>', methods=['POST'])
@login_required
def admin_cancel(id):
    """管理员取消维修申请"""
    if not current_user.is_admin():
        flash('您无权执行此操作', 'danger')
        return redirect(url_for('repair.index'))
    
    repair = RepairRequest.query.get_or_404(id)
    
    # 如果维修正在处理中，恢复房源状态
    if repair.status == 'processing':
        house = House.query.get(repair.house_id)
        if house.status == 'maintenance':
            house.status = 'rented'
    
    # 标记维修申请为拒绝
    repair.status = 'rejected'
    repair.resolved_at = datetime.now()
    db.session.commit()
    
    flash('维修申请已取消', 'success')
    return redirect(url_for('repair.all_repairs'))


@bp.route('/api/my-houses')
@login_required
def api_my_houses():
    houses = []
    if current_user.is_tenant():
        leases = LeaseContract.query.filter_by(tenant_id=current_user.id, status='active').all()
        for lease in leases:
            house = House.query.get(lease.house_id)
            if house:
                # 检查是否有待处理或处理中的维修申请
                active_repair = RepairRequest.query.filter(
                    RepairRequest.house_id == house.id,
                    RepairRequest.tenant_id == current_user.id,
                    RepairRequest.status.in_(['pending', 'processing'])
                ).first()
                
                # 只有没有待处理或处理中维修申请的房源才加入列表
                if not active_repair:
                    houses.append({
                        'id': house.id,
                        'title': house.title,
                        'address': house.address
                    })
    elif current_user.is_landlord():
        for house in House.query.filter_by(landlord_id=current_user.id).all():
            houses.append({
                'id': house.id,
                'title': house.title,
                'address': house.address
            })

    return jsonify({'houses': houses})
