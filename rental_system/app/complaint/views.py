from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import json
from app import db
from app.complaint import bp
from app.models import Complaint, House, LeaseContract, Appointment, RentPayment
from app.utils.file_upload import save_upload_file, delete_file


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
        flash('只有租客可以查看投诉', 'danger')
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
        category = request.form.get('category', '')
        target_id = request.form.get('target_id', type=int)
        content = request.form.get('content', '').strip()
        images_json = request.form.get('images', '[]')

        if not house_id or not content:
            flash('请选择房源并填写投诉内容', 'danger')
            return redirect(url_for('complaint.create'))

        # 验证房源归属（租客必须有有效合同）
        active_lease = LeaseContract.query.filter_by(
            house_id=house_id, tenant_id=current_user.id, status='active').first()
        if not active_lease:
            flash('您只能为您租住的房源提交投诉', 'danger')
            return redirect(url_for('complaint.create'))

        complaint = Complaint(
            tenant_id=current_user.id,
            house_id=house_id,
            category=category,
            target_id=target_id if target_id else None,
            content=content,
            images=images_json,
            status='pending'
        )
        db.session.add(complaint)
        db.session.commit()

        flash('投诉已提交，我们会尽快处理', 'success')
        return redirect(url_for('complaint.my_complaints'))

    # GET — 获取租客的有效合住房源列表
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

    # 权限检查
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

    # 获取关联目标信息
    target_info = _get_target_info(complaint)
    return render_template('complaint/detail.html', complaint=complaint, target_info=target_info)


@bp.route('/process/<int:id>', methods=['GET', 'POST'])
@login_required
def process(id):
    complaint = Complaint.query.get_or_404(id)

    # 权限检查
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

        if action == 'approve':
            complaint.status = 'approved'
            complaint.response = response
            complaint.resolved_at = datetime.now()
            flash('投诉已通过处理', 'success')
        elif action == 'reject':
            reject_reason = request.form.get('reject_reason', '').strip()
            if not reject_reason:
                flash('请填写驳回原因', 'danger')
                return render_template('complaint/process.html', complaint=complaint)
            complaint.status = 'rejected'
            complaint.response = response
            complaint.reject_reason = reject_reason
            complaint.resolved_at = datetime.now()
            flash('投诉已驳回', 'success')

        db.session.commit()
        return redirect(url_for('complaint.index'))

    target_info = _get_target_info(complaint)
    return render_template('complaint/process.html', complaint=complaint, target_info=target_info)


@bp.route('/cancel/<int:id>', methods=['POST'])
@login_required
def cancel(id):
    complaint = Complaint.query.get_or_404(id)

    if current_user.id != complaint.tenant_id:
        flash('您无权取消此投诉', 'danger')
        return redirect(url_for('complaint.my_complaints'))

    if complaint.status != 'pending':
        flash('当前状态不允许取消', 'danger')
        return redirect(url_for('complaint.my_complaints'))

    db.session.delete(complaint)
    db.session.commit()
    flash('已取消投诉', 'success')
    return redirect(url_for('complaint.my_complaints'))


# ==================== AJAX 接口 ====================

@bp.route('/api/tenant-houses')
@login_required
def api_tenant_houses():
    """获取租客有效合同关联的房源"""
    if not current_user.is_tenant():
        return jsonify({'houses': []})

    leases = LeaseContract.query.filter_by(tenant_id=current_user.id, status='active').all()
    houses = []
    for lease in leases:
        house = House.query.get(lease.house_id)
        if house:
            houses.append({'id': house.id, 'title': house.title, 'address': house.address})
    return jsonify({'houses': houses})


@bp.route('/api/targets')
@login_required
def api_targets():
    """根据投诉类型获取可选目标（预约/合同/付款记录）"""
    if not current_user.is_tenant():
        return jsonify({'targets': []})

    category = request.args.get('category', '')
    house_id = request.args.get('house_id', type=int)

    targets = []
    if category == 'appointment':
        query = Appointment.query.filter_by(tenant_id=current_user.id)
        if house_id:
            query = query.filter_by(house_id=house_id)
        apps = query.order_by(Appointment.created_at.desc()).limit(50).all()
        for a in apps:
            targets.append({
                'id': a.id,
                'title': f'预约看房 #{a.id} - {a.appointment_time.strftime("%Y-%m-%d %H:%M") if a.appointment_time else "待定"}',
                'status': a.status,
                'house_title': a.house.title if a.house else ''
            })
    elif category == 'contract':
        query = LeaseContract.query.filter_by(tenant_id=current_user.id)
        if house_id:
            query = query.filter_by(house_id=house_id)
        contracts = query.order_by(LeaseContract.created_at.desc()).limit(50).all()
        for c in contracts:
            targets.append({
                'id': c.id,
                'title': f'合同 #{c.id} - {c.start_date} 至 {c.end_date}',
                'status': c.status,
                'house_title': c.house.title if c.house else ''
            })
    elif category == 'rent':
        contracts = LeaseContract.query.filter_by(tenant_id=current_user.id)
        if house_id:
            contracts = contracts.filter_by(house_id=house_id)
        contract_ids = [c.id for c in contracts.all()]
        if contract_ids:
            payments = RentPayment.query.filter(
                RentPayment.contract_id.in_(contract_ids)
            ).order_by(RentPayment.due_date.desc()).limit(50).all()
            for p in payments:
                targets.append({
                    'id': p.id,
                    'title': f'账单 #{p.id} - ¥{p.amount:.2f} (到期: {p.due_date.strftime("%Y-%m-%d") if p.due_date else ""})',
                    'status': p.status,
                    'house_title': p.contract.house.title if p.contract and p.contract.house else ''
                })

    return jsonify({'targets': targets})


@bp.route('/api/temp-upload', methods=['POST'])
@login_required
def temp_upload():
    """投诉图片临时上传"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有上传文件'})
    
    file = request.files['file']
    if not file.filename:
        return jsonify({'success': False, 'message': '文件名为空'})
    
    filepath = save_upload_file(file, subfolder='uploads')
    if not filepath:
        return jsonify({'success': False, 'message': '文件类型不允许或保存失败'})
    
    return jsonify({'success': True, 'url': filepath})


# ==================== 工具函数 ====================

def _get_target_info(complaint):
    """获取投诉关联目标的详细信息"""
    if not complaint.category or not complaint.target_id:
        return None
    
    if complaint.category == 'appointment':
        target = Appointment.query.get(complaint.target_id)
        if target:
            return {
                'type': '看房预约',
                'id': target.id,
                'detail': f'预约时间: {target.appointment_time.strftime("%Y-%m-%d %H:%M") if target.appointment_time else "待定"}',
                'status': target.status
            }
    elif complaint.category == 'contract':
        target = LeaseContract.query.get(complaint.target_id)
        if target:
            return {
                'type': '租赁合同',
                'id': target.id,
                'detail': f'租期: {target.start_date} 至 {target.end_date}, 租金: ¥{target.rent_amount:.2f}',
                'status': target.status
            }
    elif complaint.category == 'rent':
        target = RentPayment.query.get(complaint.target_id)
        if target:
            return {
                'type': '租金账单',
                'id': target.id,
                'detail': f'金额: ¥{target.amount:.2f}, 到期日: {target.due_date.strftime("%Y-%m-%d") if target.due_date else ""}',
                'status': target.status
            }
    return None
