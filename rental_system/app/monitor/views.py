from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func
from app import db
from app.monitor import bp
from app.models import SystemLog, UserActivity, User, House, LeaseContract
from app.utils import log_action, record_activity


@bp.route('/')
@login_required
def index():
    if not current_user.is_admin():
        flash('只有管理员可以访问系统监控', 'danger')
        return redirect(url_for('house.index'))
    return redirect(url_for('monitor.system_logs'))


@bp.route('/system-logs')
@login_required
def system_logs():
    if not current_user.is_admin():
        flash('只有管理员可以访问系统监控', 'danger')
        return redirect(url_for('house.index'))

    page = request.args.get('page', 1, type=int)
    action = request.args.get('action', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    query = SystemLog.query

    if action:
        query = query.filter(SystemLog.action.like(f'%{action}%'))

    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(SystemLog.created_at >= start)
        except ValueError:
            pass

    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(SystemLog.created_at < end)
        except ValueError:
            pass

    logs = query.order_by(SystemLog.created_at.desc()).paginate(page=page, per_page=50)
    return render_template('monitor/logs.html', logs=logs)


@bp.route('/user-activities')
@login_required
def user_activities():
    if not current_user.is_admin():
        flash('只有管理员可以访问系统监控', 'danger')
        return redirect(url_for('house.index'))

    page = request.args.get('page', 1, type=int)
    action_type = request.args.get('action_type', '')
    days = request.args.get('days', 30, type=int)

    query = UserActivity.query

    if action_type:
        query = query.filter_by(action_type=action_type)

    if days:
        start_date = datetime.now() - timedelta(days=days)
        query = query.filter(UserActivity.timestamp >= start_date)

    activities = query.order_by(UserActivity.timestamp.desc()).paginate(page=page, per_page=50)

    action_types = db.session.query(UserActivity.action_type).distinct().all()
    action_types = [a[0] for a in action_types]

    return render_template('monitor/user_activities.html',
                          activities=activities,
                          action_types=action_types,
                          days=days,
                          action_type=action_type)


@bp.route('/users')
@login_required
def users():
    if not current_user.is_admin():
        flash('只有管理员可以访问系统监控', 'danger')
        return redirect(url_for('house.index'))

    page = request.args.get('page', 1, type=int)
    role = request.args.get('role', '')
    status = request.args.get('status', '')

    query = User.query

    if role:
        query = query.filter_by(role=role)

    if status:
        query = query.filter_by(status=status)

    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)

    return render_template('monitor/users.html', users=users, role=role, status=status)


@bp.route('/toggle-user-status/<int:id>', methods=['POST'])
@login_required
def toggle_user_status(id):
    if not current_user.is_admin():
        flash('只有管理员可以操作用户状态', 'danger')
        return redirect(url_for('monitor.users'))

    user = User.query.get_or_404(id)

    if user.id == current_user.id:
        flash('不能修改自己的状态', 'danger')
        return redirect(url_for('monitor.users'))

    user.status = 'inactive' if user.status == 'active' else 'active'
    new_status = user.status
    db.session.commit()

    log_action('切换用户状态', user_id=current_user.id, details={'target_user_id': user.id, 'username': user.username, 'new_status': new_status})
    flash(f'用户 {user.username} 状态已更新', 'success')
    return redirect(url_for('monitor.users'))


@bp.route('/system-stats')
@login_required
def system_stats():
    if not current_user.is_admin():
        flash('只有管理员可以访问系统监控', 'danger')
        return redirect(url_for('house.index'))

    total_users = User.query.count()
    active_users = User.query.filter_by(status='active').count()
    total_houses = House.query.count()
    available_houses = House.query.filter_by(status='available').count()
    rented_houses = House.query.filter_by(status='rented').count()
    total_contracts = LeaseContract.query.count()
    active_contracts = LeaseContract.query.filter_by(status='active').count()

    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    daily_logs = SystemLog.query.filter(SystemLog.created_at >= today).count()
    weekly_logs = SystemLog.query.filter(SystemLog.created_at >= week_ago).count()
    monthly_logs = SystemLog.query.filter(SystemLog.created_at >= month_ago).count()

    daily_activities = UserActivity.query.filter(UserActivity.timestamp >= today).count()
    weekly_activities = UserActivity.query.filter(UserActivity.timestamp >= week_ago).count()
    monthly_activities = UserActivity.query.filter(UserActivity.timestamp >= month_ago).count()

    top_actions = db.session.query(
        SystemLog.action,
        func.count(SystemLog.id).label('count')
    ).filter(SystemLog.created_at >= month_ago).group_by(SystemLog.action).order_by(
        func.count(SystemLog.id).desc()
    ).limit(10).all()

    return render_template('monitor/system_stats.html',
                          total_users=total_users,
                          active_users=active_users,
                          total_houses=total_houses,
                          available_houses=available_houses,
                          rented_houses=rented_houses,
                          total_contracts=total_contracts,
                          active_contracts=active_contracts,
                          daily_logs=daily_logs,
                          weekly_logs=weekly_logs,
                          monthly_logs=monthly_logs,
                          daily_activities=daily_activities,
                          weekly_activities=weekly_activities,
                          monthly_activities=monthly_activities,
                          top_actions=top_actions)


@bp.route('/api/log-stats')
@login_required
def api_log_stats():
    if not current_user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403

    days = request.args.get('days', 7, type=int)
    start_date = datetime.now() - timedelta(days=days)

    daily_counts = db.session.query(
        func.date(SystemLog.created_at).label('date'),
        func.count(SystemLog.id).label('count')
    ).filter(SystemLog.created_at >= start_date).group_by(
        func.date(SystemLog.created_at)
    ).all()

    data = [{'date': str(d[0]), 'count': d[1]} for d in daily_counts]
    return jsonify({'data': data})


@bp.route('/api/activity-stats')
@login_required
def api_activity_stats():
    if not current_user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403

    days = request.args.get('days', 7, type=int)
    start_date = datetime.now() - timedelta(days=days)

    hourly_counts = db.session.query(
        func.hour(UserActivity.timestamp).label('hour'),
        func.count(UserActivity.id).label('count')
    ).filter(UserActivity.timestamp >= start_date).group_by(
        func.hour(UserActivity.timestamp)
    ).all()

    data = [{'hour': h[0], 'count': h[1]} for h in hourly_counts]
    return jsonify({'data': data})



