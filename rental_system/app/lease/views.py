from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from app.lease import bp
from app.models import Appointment, LeaseContract, RentPayment, House, User


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

    return render_template('lease/create_appointment.html', house=house)


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
        query = LeaseContract.query.filter_by(tenant_id=current_user.id)

    if status:
        query = query.filter_by(status=status)

    contracts = query.order_by(LeaseContract.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('lease/contracts.html', contracts=contracts)


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


@bp.route('/sign-contract/<int:id>', methods=['POST'])
@login_required
def sign_contract(id):
    contract = LeaseContract.query.get_or_404(id)

    if current_user.id not in [contract.tenant_id, contract.landlord_id]:
        flash('无权签署此合同', 'danger')
        return redirect(url_for('lease.contracts'))

    if contract.status not in ['pending']:
        flash('此合同状态不允许签署', 'danger')
        return redirect(url_for('lease.contracts'))

    if current_user.is_tenant() and contract.status == 'pending':
        contract.status = 'active'
        house = House.query.get(contract.house_id)
        house.status = 'rented'
        db.session.commit()

        next_due = contract.start_date
        while next_due < contract.end_date:
            if contract.payment_method == 'monthly':
                next_due = datetime(next_due.year, next_due.month + 1 if next_due.month < 12 else 1,
                                   next_due.day if next_due.month < 12 else 1).date()
                if next_due.month == 1 and next_due.day > 28:
                    next_due = datetime(next_due.year + 1, 1, 1).date()
            elif contract.payment_method == 'quarterly':
                next_due = datetime(next_due.year, next_due.month + 3 if next_due.month < 10 else 1,
                                   next_due.day if next_due.month < 10 else 1).date()
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
