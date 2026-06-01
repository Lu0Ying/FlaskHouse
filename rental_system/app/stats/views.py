from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from app import db
from app.stats import bp
from app.models import House, LeaseContract, RentPayment, User, UserActivity, Appointment, RepairRequest


@bp.route('/')
@login_required
def index():
    if current_user.is_admin():
        return redirect(url_for('stats.admin_dashboard'))
    elif current_user.is_landlord():
        return redirect(url_for('stats.landlord_dashboard'))
    else:
        return redirect(url_for('stats.tenant_dashboard'))


@bp.route('/admin-dashboard')
@login_required
def admin_dashboard():
    total_houses = House.query.count()
    available_houses = House.query.filter_by(status='available').count()
    rented_houses = House.query.filter_by(status='rented').count()
    maintenance_houses = House.query.filter_by(status='maintenance').count()

    total_users = User.query.count()
    total_landlords = User.query.filter_by(role='landlord').count()
    total_tenants = User.query.filter_by(role='tenant').count()
    active_users = User.query.filter_by(status='active').count()

    active_contracts = LeaseContract.query.filter_by(status='active').count()
    total_contracts = LeaseContract.query.count()

    total_revenue = db.session.query(func.sum(RentPayment.amount)).filter_by(status='paid').scalar() or 0
    monthly_revenue = db.session.query(func.sum(RentPayment.amount)).filter(
        RentPayment.status == 'paid',
        RentPayment.paid_date >= datetime.now().replace(day=1).date()
    ).scalar() or 0

    overdue_payments = RentPayment.query.filter_by(status='unpaid').filter(
        RentPayment.due_date < datetime.now().date()
    ).count()

    recent_activities = UserActivity.query.order_by(UserActivity.timestamp.desc()).limit(10).all()

    return render_template('stats/admin_dashboard.html',
                          total_houses=total_houses,
                          available_houses=available_houses,
                          rented_houses=rented_houses,
                          maintenance_houses=maintenance_houses,
                          total_users=total_users,
                          total_landlords=total_landlords,
                          total_tenants=total_tenants,
                          active_users=active_users,
                          active_contracts=active_contracts,
                          total_contracts=total_contracts,
                          total_revenue=total_revenue,
                          monthly_revenue=monthly_revenue,
                          overdue_payments=overdue_payments,
                          recent_activities=recent_activities)


@bp.route('/landlord-dashboard')
@login_required
def landlord_dashboard():
    my_houses = House.query.filter_by(landlord_id=current_user.id)
    total_houses = my_houses.count()
    available_houses = my_houses.filter_by(status='available').count()
    rented_houses = my_houses.filter_by(status='rented').count()
    maintenance_houses = my_houses.filter_by(status='maintenance').count()

    my_contracts = LeaseContract.query.filter_by(landlord_id=current_user.id)
    active_contracts = my_contracts.filter_by(status='active').count()

    my_revenue = db.session.query(func.sum(RentPayment.amount)).join(LeaseContract).filter(
        LeaseContract.landlord_id == current_user.id,
        RentPayment.status == 'paid'
    ).scalar() or 0

    monthly_revenue = db.session.query(func.sum(RentPayment.amount)).join(LeaseContract).filter(
        LeaseContract.landlord_id == current_user.id,
        RentPayment.status == 'paid',
        RentPayment.paid_date >= datetime.now().replace(day=1).date()
    ).scalar() or 0

    pending_repairs = RepairRequest.query.join(House).filter(
        House.landlord_id == current_user.id,
        RepairRequest.status.in_(['pending', 'processing'])
    ).count()

    pending_appointments = Appointment.query.filter_by(
        landlord_id=current_user.id,
        status='pending'
    ).count()

    return render_template('stats/landlord_dashboard.html',
                          total_houses=total_houses,
                          available_houses=available_houses,
                          rented_houses=rented_houses,
                          maintenance_houses=maintenance_houses,
                          active_contracts=active_contracts,
                          my_revenue=my_revenue,
                          monthly_revenue=monthly_revenue,
                          pending_repairs=pending_repairs,
                          pending_appointments=pending_appointments)


@bp.route('/tenant-dashboard')
@login_required
def tenant_dashboard():
    my_contracts = LeaseContract.query.filter_by(tenant_id=current_user.id, status='active')
    active_contracts = my_contracts.count()

    my_rentals = []
    for contract in my_contracts.all():
        house = House.query.get(contract.house_id)
        if house:
            my_rentals.append({
                'house': house,
                'contract': contract
            })

    upcoming_payments = RentPayment.query.join(LeaseContract).filter(
        LeaseContract.tenant_id == current_user.id,
        RentPayment.status == 'unpaid'
    ).order_by(RentPayment.due_date).limit(5).all()

    my_repairs = RepairRequest.query.filter_by(
        tenant_id=current_user.id
    ).filter(RepairRequest.status.in_(['pending', 'processing'])).count()

    return render_template('stats/tenant_dashboard.html',
                          active_contracts=active_contracts,
                          my_rentals=my_rentals,
                          upcoming_payments=upcoming_payments,
                          my_repairs=my_repairs)


@bp.route('/house-stats')
@login_required
def house_stats():
    if not current_user.is_admin() and not current_user.is_landlord():
        flash('无权访问此页面', 'danger')
        return redirect(url_for('stats.index'))

    if current_user.is_landlord():
        houses = House.query.filter_by(landlord_id=current_user.id).all()
    else:
        houses = House.query.all()

    house_data = []
    for house in houses:
        contracts = LeaseContract.query.filter_by(house_id=house.id).all()
        total_days = 0
        rented_days = 0

        for contract in contracts:
            start = contract.start_date
            end = min(contract.end_date, datetime.now().date())
            if contract.status == 'active':
                end = datetime.now().date()
            total_days += (end - start).days if end > start else 0
            if contract.status == 'active':
                rented_days += (end - start).days if end > start else 0

        if total_days > 0:
            occupancy_rate = (rented_days / total_days) * 100
        else:
            occupancy_rate = 0

        house_data.append({
            'house': house,
            'total_contracts': len(contracts),
            'active_contract': LeaseContract.query.filter_by(house_id=house.id, status='active').first(),
            'occupancy_rate': occupancy_rate
        })

    return render_template('stats/house_stats.html', house_data=house_data)


@bp.route('/revenue-stats')
@login_required
def revenue_stats():
    if not current_user.is_admin() and not current_user.is_landlord():
        flash('无权访问此页面', 'danger')
        return redirect(url_for('stats.index'))

    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)

    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()

    if current_user.is_landlord():
        query = RentPayment.query.join(LeaseContract).filter(
            LeaseContract.landlord_id == current_user.id,
            RentPayment.status == 'paid'
        )
    else:
        query = RentPayment.query.filter_by(status='paid')

    monthly_revenue = query.filter(
        RentPayment.paid_date >= start_date,
        RentPayment.paid_date < end_date
    ).all()

    total = sum(p.amount for p in monthly_revenue)

    daily_revenue = {}
    for payment in monthly_revenue:
        day = payment.paid_date.day
        daily_revenue[day] = daily_revenue.get(day, 0) + payment.amount

    chart_data = [{'day': d, 'amount': a} for d, a in sorted(daily_revenue.items())]

    return render_template('stats/revenue_stats.html',
                          year=year,
                          month=month,
                          total=total,
                          chart_data=chart_data)


@bp.route('/user-stats')
@login_required
def user_stats():
    if not current_user.is_admin():
        flash('无权访问此页面', 'danger')
        return redirect(url_for('stats.index'))

    days = request.args.get('days', 30, type=int)
    start_date = datetime.now() - timedelta(days=days)

    daily_active = db.session.query(
        func.date(UserActivity.timestamp).label('date'),
        func.count(func.distinct(UserActivity.user_id)).label('count')
    ).filter(UserActivity.timestamp >= start_date).group_by(
        func.date(UserActivity.timestamp)
    ).all()

    chart_data = [{'date': str(d[0]), 'count': d[1]} for d in daily_active]

    top_users = db.session.query(
        User.username,
        func.count(UserActivity.id).label('activity_count')
    ).join(UserActivity).group_by(User.id, User.username).order_by(
        func.count(UserActivity.id).desc()
    ).limit(10).all()

    return render_template('stats/user_stats.html',
                          days=days,
                          chart_data=chart_data,
                          top_users=top_users)


@bp.route('/api/revenue-monthly')
@login_required
def api_revenue_monthly():
    if not current_user.is_admin() and not current_user.is_landlord():
        return jsonify({'error': 'Unauthorized'}), 403

    year = request.args.get('year', datetime.now().year, type=int)

    monthly_data = []
    for month in range(1, 13):
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date()
        else:
            end_date = datetime(year, month + 1, 1).date()

        if current_user.is_landlord():
            amount = db.session.query(func.sum(RentPayment.amount)).join(LeaseContract).filter(
                LeaseContract.landlord_id == current_user.id,
                RentPayment.status == 'paid',
                RentPayment.paid_date >= start_date,
                RentPayment.paid_date < end_date
            ).scalar() or 0
        else:
            amount = db.session.query(func.sum(RentPayment.amount)).filter(
                RentPayment.status == 'paid',
                RentPayment.paid_date >= start_date,
                RentPayment.paid_date < end_date
            ).scalar() or 0

        monthly_data.append({'month': month, 'amount': float(amount)})

    return jsonify({'year': year, 'data': monthly_data})


@bp.route('/api/house-occupancy')
@login_required
def api_house_occupancy():
    if current_user.is_landlord():
        houses = House.query.filter_by(landlord_id=current_user.id).all()
    elif current_user.is_admin():
        houses = House.query.all()
    else:
        return jsonify({'error': 'Unauthorized'}), 403

    data = []
    for house in houses:
        contracts = LeaseContract.query.filter_by(house_id=house.id).all()
        total_days = 0
        rented_days = 0

        for contract in contracts:
            start = contract.start_date
            end = min(contract.end_date, datetime.now().date())
            if contract.status == 'active':
                end = datetime.now().date()
            days = (end - start).days if end > start else 0
            total_days += days
            if contract.status in ['active', 'terminated']:
                rented_days += days

        occupancy = (rented_days / total_days * 100) if total_days > 0 else 0
        data.append({
            'house_id': house.id,
            'title': house.title,
            'occupancy': round(occupancy, 1)
        })

    return jsonify({'data': data})
