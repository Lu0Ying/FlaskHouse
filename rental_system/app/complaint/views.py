from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.complaint import bp
from app.models import Complaint, House, LeaseContract


@bp.route('/')
@login_required
def index():
    if current_user.is_tenant():
        return redirect(url_for('complaint.my_complaints'))
    elif current_user.is_landlord():
        return redirect(url_for('complaint.landlord_complaints'))
    else:
        return redirect(url_for('complaint.all_complaints'))


@bp.route('/my-complaints')
@login_required
def my_complaints():
    if not current_user.is_tenant():
        flash('只有租客可以提交投诉', 'danger')
        return redirect(url_for('house.index'))

    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')

    query = Complaint.query.filter_by(tenant_id=current_user.id)

    if status:
        query = query.filter_by(status=status)

    complaints = query.order_by(Complaint.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('complaint/my_complaints.html', complaints=complaints)


@bp.route('/landlord-complaints')
@login_required
def landlord_complaints():
    if not current_user.is_landlord():
        flash('只有房东可以查看投诉', 'danger')
        return redirect(url_for('house.index'))

    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')

    house_ids = [h.id for h in House.query.filter_by(landlord_id=current_user.id).all()]
    query = Complaint.query.filter(Complaint.house_id.in_(house_ids))

    if status:
        query = query.filter_by(status=status)

    complaints = query.order_by(Complaint.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('complaint/landlord_complaints.html', complaints=complaints)


@bp.route('/all-complaints')
@login_required
def all_complaints():
    if not current_user.is_admin():
        flash('只有管理员可以查看所有投诉', 'danger')
        return redirect(url_for('house.index'))

    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')

    query = Complaint.query

    if status:
        query = query.filter_by(status=status)

    complaints = query.order_by(Complaint.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('complaint/all_complaints.html', complaints=complaints)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.is_tenant():
        flash('只有租客可以提交投诉', 'danger')
        return redirect(url_for('house.index'))

    if request.method == 'POST':
        house_id = request.form.get('house_id', type=int)
        target_type = request.form.get('target_type', '')
        content = request.form.get('content', '').strip()

        if not house_id or not content:
            flash('请选择房源并填写投诉内容', 'danger')
            return redirect(url_for('complaint.create'))

        house = House.query.get(house_id)
        if not house:
            flash('房源不存在', 'danger')
            return redirect(url_for('complaint.create'))

        active_lease = LeaseContract.query.filter_by(
            house_id=house_id, tenant_id=current_user.id, status='active').first()
        if not active_lease:
            flash('您只能为您租住的房源提交投诉', 'danger')
            return redirect(url_for('complaint.create'))

        complaint = Complaint(
            tenant_id=current_user.id,
            house_id=house_id,
            target_type=target_type,
            content=content,
            status='pending'
        )
        db.session.add(complaint)
        db.session.commit()

        flash('投诉已提交，我们会尽快处理', 'success')
        return redirect(url_for('complaint.my_complaints'))

    leases = LeaseContract.query.filter_by(tenant_id=current_user.id, status='active').all()
    houses = []
    for lease in leases:
        house = House.query.get(lease.house_id)
        if house:
            houses.append(house)

    return render_template('complaint/create.html', houses=houses)


@bp.route('/detail/<int:id>')
@login_required
def detail(id):
    complaint = Complaint.query.get_or_404(id)

    if current_user.id == complaint.tenant_id:
        pass
    elif current_user.is_landlord():
        house = House.query.get(complaint.house_id)
        if house.landlord_id != current_user.id and not current_user.is_admin():
            flash('您无权查看此投诉', 'danger')
            return redirect(url_for('complaint.index'))
    elif not current_user.is_admin():
        flash('您无权查看此投诉', 'danger')
        return redirect(url_for('complaint.index'))

    return render_template('complaint/detail.html', complaint=complaint)


@bp.route('/process/<int:id>', methods=['GET', 'POST'])
@login_required
def process(id):
    complaint = Complaint.query.get_or_404(id)

    if current_user.is_landlord():
        house = House.query.get(complaint.house_id)
        if house.landlord_id != current_user.id:
            flash('您无权处理此投诉', 'danger')
            return redirect(url_for('complaint.landlord_complaints'))
    elif not current_user.is_admin():
        flash('您无权处理此投诉', 'danger')
        return redirect(url_for('complaint.index'))

    if request.method == 'POST':
        action = request.form.get('action')
        response = request.form.get('response', '').strip()

        if action == 'process':
            complaint.status = 'processing'
            if response:
                complaint.response = response
            flash('投诉正在处理中', 'success')
        elif action == 'resolve':
            complaint.status = 'resolved'
            complaint.response = response
            complaint.resolved_at = datetime.now()
            flash('投诉已处理完成', 'success')
        elif action == 'reject':
            complaint.status = 'rejected'
            complaint.response = response
            complaint.resolved_at = datetime.now()
            flash('投诉已驳回', 'success')

        db.session.commit()
        return redirect(url_for('complaint.landlord_complaints'))

    return render_template('complaint/process.html', complaint=complaint)


@bp.route('/cancel/<int:id>', methods=['POST'])
@login_required
def cancel(id):
    complaint = Complaint.query.get_or_404(id)

    if current_user.id != complaint.tenant_id:
        flash('您无权取消此投诉', 'danger')
        return redirect(url_for('complaint.my_complaints'))

    if complaint.status not in ['pending']:
        flash('当前状态不允许取消', 'danger')
        return redirect(url_for('complaint.my_complaints'))

    db.session.delete(complaint)
    db.session.commit()

    flash('已取消投诉', 'success')
    return redirect(url_for('complaint.my_complaints'))


@bp.route('/api/tenant-houses')
@login_required
def api_tenant_houses():
    if not current_user.is_tenant():
        return jsonify({'houses': []})

    leases = LeaseContract.query.filter_by(tenant_id=current_user.id, status='active').all()
    houses = []
    for lease in leases:
        house = House.query.get(lease.house_id)
        if house:
            houses.append({
                'id': house.id,
                'title': house.title,
                'address': house.address
            })

    return jsonify({'houses': houses})
