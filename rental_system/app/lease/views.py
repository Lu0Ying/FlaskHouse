from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date
from app import db
from app.lease import bp
from app.models import Appointment, LeaseContract, RentPayment, House, User


@bp.context_processor
def utility_processor():
    """添加工具函数到模板上下文"""
    return dict(now=datetime.now)


@bp.route('/')
@login_required
def index():
    if current_user.is_admin():
        return redirect(url_for('lease.contracts'))
    elif current_user.is_landlord():
        return redirect(url_for('lease.landlord_appointments'))
    else:
        return redirect(url_for('lease.my_appointments'))


@bp.route('/appointments')
@login_required
def appointments():
    if current_user.is_tenant():
        return redirect(url_for('lease.my_appointments'))
    return redirect(url_for('lease.landlord_appointments'))


@bp.route('/my-appointments')
@login_required
def my_appointments():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')

    query = Appointment.query.filter_by(tenant_id=current_user.id)

    if status:
        query = query.filter_by(status=status)

    appointments = query.order_by(Appointment.appointment_time.desc()).paginate(page=page, per_page=10)
    return render_template('lease/my_appointments.html', appointments=appointments)


@bp.route('/landlord-appointments')
@login_required
def landlord_appointments():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')

    query = Appointment.query.filter_by(landlord_id=current_user.id)

    if status:
        query = query.filter_by(status=status)

    appointments = query.order_by(Appointment.appointment_time.desc()).paginate(page=page, per_page=10)
    return render_template('lease/landlord_appointments.html', appointments=appointments)


@bp.route('/create-appointment/<int:house_id>', methods=['GET', 'POST'])
@login_required
def create_appointment(house_id):
    house = House.query.get_or_404(house_id)

    if request.method == 'POST':
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')
        remark = request.form.get('remark', '')

        try:
            appointment_datetime = datetime.strptime(f'{appointment_date} {appointment_time}', '%Y-%m-%d %H:%M')
        except ValueError:
            flash('日期或时间格式不正确', 'danger')
            return redirect(url_for('lease.create_appointment', house_id=house_id))

        if appointment_datetime < datetime.now():
            flash('预约时间不能早于当前时间', 'danger')
            return redirect(url_for('lease.create_appointment', house_id=house_id))

        existing = Appointment.query.filter_by(house_id=house_id, status='pending').first()
        if existing:
            flash('该房源已有待处理的预约，请等待处理', 'warning')
            return redirect(url_for('house.detail', id=house_id))

        appointment = Appointment(
            house_id=house_id,
            tenant_id=current_user.id,
            landlord_id=house.landlord_id,
            appointment_time=appointment_datetime,
            remark=remark,
            status='pending'
        )
        db.session.add(appointment)
        db.session.commit()

        flash('看房预约已提交，请等待房东确认', 'success')
        return redirect(url_for('lease.my_appointments'))

    from datetime import date
    today = date.today().isoformat()
    return render_template('lease/create_appointment.html', house=house, today=today)


@bp.route('/confirm-appointment/<int:id>', methods=['POST'])
@login_required
def confirm_appointment(id):
    appointment = Appointment.query.get_or_404(id)

    if current_user.id != appointment.landlord_id:
        flash('无权操作', 'danger')
        return redirect(url_for('lease.landlord_appointments'))

    appointment.status = 'confirmed'
    db.session.commit()
    flash('已确认看房预约', 'success')
    return redirect(url_for('lease.landlord_appointments'))


@bp.route('/cancel-appointment/<int:id>', methods=['POST'])
@login_required
def cancel_appointment(id):
    appointment = Appointment.query.get_or_404(id)

    if current_user.id not in [appointment.tenant_id, appointment.landlord_id]:
        flash('无权操作', 'danger')
        return redirect(url_for('lease.my_appointments'))

    appointment.status = 'cancelled'
    db.session.commit()
    flash('已取消预约', 'success')

    if current_user.is_landlord():
        return redirect(url_for('lease.landlord_appointments'))
    return redirect(url_for('lease.my_appointments'))


@bp.route('/complete-appointment/<int:id>', methods=['POST'])
@login_required
def complete_appointment(id):
    appointment = Appointment.query.get_or_404(id)

    if current_user.id != appointment.landlord_id:
        flash('无权操作', 'danger')
        return redirect(url_for('lease.landlord_appointments'))

    appointment.status = 'completed'
    db.session.commit()
    flash('已完成看房', 'success')
    return redirect(url_for('lease.landlord_appointments'))


@bp.route('/contracts')
@login_required
def contracts():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')

    if current_user.is_admin():
        query = LeaseContract.query
    elif current_user.is_landlord():
        query = LeaseContract.query.filter_by(landlord_id=current_user.id)
    else:
        # 租客：显示自己发起的合同
        query = LeaseContract.query.filter_by(tenant_id=current_user.id)

    if status:
        query = query.filter_by(status=status)

    contracts_list = query.order_by(LeaseContract.created_at.desc()).paginate(page=page, per_page=10)
    
    # 根据用户角色选择不同的模板
    if current_user.is_tenant():
        return render_template('lease/tenant_contracts.html', contracts=contracts_list)
    else:
        return render_template('lease/contracts.html', contracts=contracts_list)


@bp.route('/create-contract/<int:house_id>', methods=['GET', 'POST'])
@login_required
def create_contract(house_id):
    house = House.query.get_or_404(house_id)

    if request.method == 'POST':
        tenant_id = request.form.get('tenant_id', type=int)
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        rent_amount = request.form.get('rent_amount', type=float)
        deposit_amount = request.form.get('deposit_amount', type=float)
        payment_method = request.form.get('payment_method', 'monthly')

        if current_user.is_landlord():
            landlord_id = current_user.id
        elif current_user.is_tenant():
            tenant_id = current_user.id
            landlord_id = house.landlord_id
        else:
            landlord_id = request.form.get('landlord_id', type=int)

        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            flash('日期格式不正确', 'danger')
            return redirect(url_for('lease.create_contract', house_id=house_id))

        if start >= end:
            flash('结束日期必须晚于开始日期', 'danger')
            return redirect(url_for('lease.create_contract', house_id=house_id))

        contract = LeaseContract(
            house_id=house_id,
            tenant_id=tenant_id,
            landlord_id=landlord_id,
            start_date=start,
            end_date=end,
            rent_amount=rent_amount,
            deposit_amount=deposit_amount,
            payment_method=payment_method,
            status='pending',
            signed_at=datetime.now()
        )
        db.session.add(contract)
        db.session.commit()

        flash('合同已创建，请等待对方确认签署', 'success')
        return redirect(url_for('lease.contracts'))

    tenants = User.query.filter_by(role='tenant').all() if current_user.is_admin() else []
    return render_template('lease/create_contract.html', house=house, tenants=tenants)


@bp.route('/create-contract-tenant', methods=['GET', 'POST'])
@bp.route('/create-contract-tenant/<int:house_id>', methods=['GET', 'POST'])
@login_required
def create_contract_tenant(house_id=None):
    """租客发起租赁合同"""
    if not current_user.is_tenant():
        flash('只有租客可以发起合同', 'danger')
        return redirect(url_for('lease.contracts'))

    preselected_house = None
    if house_id:
        preselected_house = House.query.get_or_404(house_id)
        # 检查房源是否可用
        if preselected_house.status != 'available':
            flash('该房源暂不可租', 'warning')
            return redirect(url_for('house.detail', id=house_id))

    if request.method == 'POST':
        house_id = request.form.get('house_id', type=int)
        start_date = request.form.get('start_date')
        duration_months = request.form.get('duration_months', type=int)
        rent_amount = request.form.get('rent_amount', type=float)
        deposit_amount = request.form.get('deposit_amount', type=float)
        payment_method = request.form.get('payment_method', 'monthly')

        # 验证房源
        house = House.query.get_or_404(house_id)
        
        # 检查房源是否已被租出
        if house.status == 'rented':
            flash('该房源已被租出', 'danger')
            return redirect(url_for('lease.create_contract_tenant'))

        # 计算结束日期（按月）
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            # 计算结束年份和月份
            end_year = start.year + (start.month + duration_months - 1) // 12
            end_month = (start.month + duration_months - 1) % 12 + 1
            
            # 处理月末日期问题
            import calendar
            last_day = calendar.monthrange(end_year, end_month)[1]
            end_day = min(start.day, last_day)
            
            end = date(end_year, end_month, end_day)
        except (ValueError, TypeError):
            flash('日期格式不正确', 'danger')
            return redirect(url_for('lease.create_contract_tenant'))

        if start < date.today():
            flash('开始日期不能早于今天', 'danger')
            return redirect(url_for('lease.create_contract_tenant'))

        # 创建合同
        contract = LeaseContract(
            house_id=house_id,
            tenant_id=current_user.id,
            landlord_id=house.landlord_id,
            start_date=start,
            end_date=end,
            rent_amount=rent_amount,
            deposit_amount=deposit_amount,
            payment_method=payment_method,
            status='pending'
        )
        db.session.add(contract)
        db.session.commit()

        flash('合同申请已提交，请等待房东审批', 'success')
        return redirect(url_for('lease.contracts'))

    # GET请求：显示可租赁的房源列表
    houses = House.query.filter_by(status='available').all()
    today = date.today().isoformat()
    return render_template('lease/create_contract_tenant.html', 
                          houses=houses, 
                          today=today, 
                          preselected_house=preselected_house)


@bp.route('/approve-contract/<int:id>', methods=['POST'])
@login_required
def approve_contract(id):
    """房东同意合同"""
    contract = LeaseContract.query.get_or_404(id)

    if not current_user.is_landlord() or current_user.id != contract.landlord_id:
        flash('无权操作', 'danger')
        return redirect(url_for('lease.contracts'))

    if contract.status != 'pending':
        flash('合同状态不允许审批', 'danger')
        return redirect(url_for('lease.contracts'))

    # 更新合同状态为生效
    contract.status = 'active'
    
    # 更新房源状态为已租
    house = House.query.get(contract.house_id)
    house.status = 'rented'
    
    # 自动生成租金支付记录（账单）
    next_due = contract.start_date
    payment_count = 0
    
    while next_due < contract.end_date:
        # 根据支付方式计算下次付款日期
        if contract.payment_method == 'monthly':
            month = next_due.month + 1
            year = next_due.year
            if month > 12:
                month = 1
                year += 1
            # 处理月末日期问题
            import calendar
            max_day = calendar.monthrange(year, month)[1]
            day = min(next_due.day, max_day)
            next_due = datetime(year, month, day).date()
        elif contract.payment_method == 'quarterly':
            month = next_due.month + 3
            year = next_due.year
            if month > 12:
                month -= 12
                year += 1
            import calendar
            max_day = calendar.monthrange(year, month)[1]
            day = min(next_due.day, max_day)
            next_due = datetime(year, month, day).date()
        elif contract.payment_method == 'yearly':
            year = next_due.year + 1
            import calendar
            max_day = calendar.monthrange(year, next_due.month)[1]
            day = min(next_due.day, max_day)
            next_due = datetime(year, next_due.month, day).date()
        else:
            # 默认按月
            month = next_due.month + 1
            year = next_due.year
            if month > 12:
                month = 1
                year += 1
            import calendar
            max_day = calendar.monthrange(year, month)[1]
            day = min(next_due.day, max_day)
            next_due = datetime(year, month, day).date()
        
        # 如果下次付款日期在合同有效期内，创建账单
        if next_due < contract.end_date:
            payment = RentPayment(
                contract_id=contract.id,
                amount=contract.rent_amount,
                due_date=next_due,
                status='unpaid'
            )
            db.session.add(payment)
            payment_count += 1
    
    db.session.commit()

    flash(f'已同意出租请求，合同已生效，已生成 {payment_count} 期租金账单', 'success')
    return redirect(url_for('lease.contracts'))


@bp.route('/reject-contract/<int:id>', methods=['POST'])
@login_required
def reject_contract(id):
    """房东拒绝合同"""
    contract = LeaseContract.query.get_or_404(id)

    if not current_user.is_landlord() or current_user.id != contract.landlord_id:
        flash('无权操作', 'danger')
        return redirect(url_for('lease.contracts'))

    if contract.status != 'pending':
        flash('合同状态不允许审批', 'danger')
        return redirect(url_for('lease.contracts'))

    # 将合同状态标记为被拒
    contract.status = 'rejected'
    db.session.commit()

    flash('已拒绝出租请求', 'success')
    return redirect(url_for('lease.contracts'))


@bp.route('/cancel-contract/<int:id>', methods=['POST'])
@login_required
def cancel_contract(id):
    """租客取消合同申请"""
    contract = LeaseContract.query.get_or_404(id)

    if not current_user.is_tenant() or current_user.id != contract.tenant_id:
        flash('无权操作', 'danger')
        return redirect(url_for('lease.contracts'))

    if contract.status != 'pending':
        flash('只能取消待审批的合同', 'danger')
        return redirect(url_for('lease.contracts'))

    db.session.delete(contract)
    db.session.commit()

    flash('已取消合同申请', 'success')
    return redirect(url_for('lease.contracts'))


@bp.route('/sign-contract/<int:id>', methods=['POST'])
@login_required
def sign_contract(id):
    """租客签署合同（保留用于兼容旧流程）"""
    contract = LeaseContract.query.get_or_404(id)

    if current_user.id not in [contract.tenant_id, contract.landlord_id]:
        flash('无权签署此合同', 'danger')
        return redirect(url_for('lease.contracts'))

    if contract.status != 'pending':
        flash('此合同状态不允许签署', 'danger')
        return redirect(url_for('lease.contracts'))

    # 如果是租客签署，需要房东审批
    if current_user.is_tenant():
        flash('合同已提交，请等待房东审批', 'success')
        return redirect(url_for('lease.contracts'))
    
    # 如果是房东签署（同意），直接生效
    if current_user.is_landlord():
        contract.status = 'active'
        house = House.query.get(contract.house_id)
        house.status = 'rented'
        db.session.commit()
        flash('合同签署成功，已生效', 'success')
        return redirect(url_for('lease.contracts'))


@bp.route('/terminate-contract/<int:id>', methods=['POST'])
@login_required
def terminate_contract(id):
    contract = LeaseContract.query.get_or_404(id)

    if current_user.id not in [contract.tenant_id, contract.landlord_id, contract.house.landlord_id]:
        flash('无权终止此合同', 'danger')
        return redirect(url_for('lease.contracts'))

    contract.status = 'terminated'
    house = House.query.get(contract.house_id)
    house.status = 'available'
    db.session.commit()

    flash('合同已终止', 'success')
    return redirect(url_for('lease.contracts'))


@bp.route('/view-contract/<int:id>')
@login_required
def view_contract(id):
    contract = LeaseContract.query.get_or_404(id)

    if current_user.id not in [contract.tenant_id, contract.landlord_id] and not current_user.is_admin():
        flash('无权查看此合同', 'danger')
        return redirect(url_for('lease.contracts'))

    return render_template('lease/view_contract.html', contract=contract)


@bp.route('/payments')
@login_required
def payments():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')

    if current_user.is_admin():
        query = RentPayment.query
    elif current_user.is_landlord():
        contract_ids = [c.id for c in LeaseContract.query.filter_by(landlord_id=current_user.id).all()]
        query = RentPayment.query.filter(RentPayment.contract_id.in_(contract_ids))
    else:
        contract_ids = [c.id for c in LeaseContract.query.filter_by(tenant_id=current_user.id).all()]
        query = RentPayment.query.filter(RentPayment.contract_id.in_(contract_ids))

    if status:
        query = query.filter_by(status=status)

    payments = query.order_by(RentPayment.due_date.desc()).paginate(page=page, per_page=20)
    return render_template('lease/payments.html', payments=payments)


@bp.route('/pay-rent/<int:id>', methods=['POST'])
@login_required
def pay_rent(id):
    payment = RentPayment.query.get_or_404(id)
    contract = LeaseContract.query.get(payment.contract_id)

    if current_user.id != contract.tenant_id:
        flash('只有租客可以支付租金', 'danger')
        return redirect(url_for('lease.payments'))

    if payment.status == 'paid':
        flash('此账单已支付', 'warning')
        return redirect(url_for('lease.payments'))

    payment.status = 'paid'
    payment.paid_date = datetime.now().date()
    payment.payment_method = request.form.get('payment_method', 'alipay')
    db.session.commit()

    flash('租金支付成功', 'success')
    return redirect(url_for('lease.payments'))


@bp.route('/remind-rent/<int:id>', methods=['POST'])
@login_required
def remind_rent(id):
    payment = RentPayment.query.get_or_404(id)
    contract = LeaseContract.query.get(payment.contract_id)

    if current_user.id != contract.landlord_id:
        flash('只有房东可以发送提醒', 'danger')
        return redirect(url_for('lease.payments'))

    flash('已向租客发送支付提醒', 'success')
    return redirect(url_for('lease.payments'))


@bp.route('/generate-payments/<int:contract_id>', methods=['POST'])
@login_required
def generate_payments(contract_id):
    contract = LeaseContract.query.get_or_404(contract_id)

    if current_user.id != contract.landlord_id and not current_user.is_admin():
        flash('无权操作', 'danger')
        return redirect(url_for('lease.contracts'))

    if contract.status != 'active':
        flash('只能为生效中的合同生成账单', 'danger')
        return redirect(url_for('lease.view_contract', id=contract_id))

    existing_count = RentPayment.query.filter_by(contract_id=contract_id).count()
    if existing_count > 0:
        flash('账单已存在，如需重新生成请先删除现有账单', 'warning')
        return redirect(url_for('lease.view_contract', id=contract_id))

    next_due = contract.start_date
    while next_due < contract.end_date:
        if contract.payment_method == 'monthly':
            month = next_due.month + 1
            year = next_due.year
            if month > 12:
                month = 1
                year += 1
            day = min(next_due.day, [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
            next_due = datetime(year, month, day).date()
        elif contract.payment_method == 'quarterly':
            month = next_due.month + 3
            year = next_due.year
            if month > 12:
                month -= 12
                year += 1
            day = min(next_due.day, [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
            next_due = datetime(year, month, day).date()
        else:
            next_due = contract.end_date

        if next_due < contract.end_date:
            payment = RentPayment(
                contract_id=contract.id,
                amount=contract.rent_amount,
                due_date=next_due,
                status='unpaid'
            )
            db.session.add(payment)

    db.session.commit()
    flash('账单已生成', 'success')
    return redirect(url_for('lease.view_contract', id=contract_id))
