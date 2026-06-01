from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.repair import bp
from app.models import RepairRequest, House, LeaseContract


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
        houses = [LeaseContract.house for LeaseContract in leases]
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

        if action == 'accept':
            repair.status = 'processing'
            flash('已接受维修申请，正在处理中', 'success')
        elif action == 'complete':
            repair.status = 'completed'
            repair.resolved_at = datetime.now()
            flash('维修已完成', 'success')
        elif action == 'reject':
            repair.status = 'rejected'
            repair.resolved_at = datetime.now()
            flash('已拒绝维修申请', 'success')

        db.session.commit()
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

    db.session.delete(repair)
    db.session.commit()

    flash('已取消维修申请', 'success')
    return redirect(url_for('repair.my_repairs'))


@bp.route('/api/my-houses')
@login_required
def api_my_houses():
    houses = []
    if current_user.is_tenant():
        leases = LeaseContract.query.filter_by(tenant_id=current_user.id, status='active').all()
        for lease in leases:
            house = House.query.get(lease.house_id)
            if house:
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
