from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import check_password_hash
from app import db
from app.auth import bp
from app.models import *
from app.forms import LoginForm, RegistrationForm
from app.utils import log_action

@bp.route('/')
def index():
    return render_template('auth/index.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('house.index'))
    
    form = LoginForm()
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if user.status != 'active':
                flash('账户已被禁用', 'danger')
                log_action('用户登录失败-账户禁用', user_id=user.id, details={'email': email})
                return render_template('auth/login.html', form=form)
            
            login_user(user, remember=remember)
            log_action('用户登录成功', user_id=user.id, details={'email': email, 'remember': remember})
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('house.index'))
        else:
            flash('邮箱或密码错误', 'danger')
            log_action('用户登录失败-密码错误', details={'email': email})
    
    return render_template('auth/login.html', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('house.index'))
    
    form = RegistrationForm()
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'tenant')
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'danger')
            return render_template('auth/register.html', form=form)
        
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'danger')
            return render_template('auth/register.html', form=form)
        
        user = User(
            username=username,
            email=email,
            role=role,
            status='active'
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        log_action('用户注册成功', user_id=user.id, details={'username': username, 'email': email, 'role': role})
        flash('注册成功，请登录', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    user_id = current_user.id
    username = current_user.username
    log_action('用户注销', user_id=user_id, details={'username': username})
    logout_user()
    flash('已退出登录', 'info')
    return redirect(url_for('house.index'))
