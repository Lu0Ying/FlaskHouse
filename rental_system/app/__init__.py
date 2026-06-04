from flask import Flask, render_template, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_mail import Mail
from config import Config
import json

# 初始化扩展
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
mail = Mail()

login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'


def create_app(config_class=Config):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    
    # 注册根路由
    @app.route('/')
    def index():
        return redirect(url_for('house.index'))
    
    # 注册蓝图
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.house import bp as house_bp
    app.register_blueprint(house_bp, url_prefix='/house')
    
    from app.user import bp as user_bp
    app.register_blueprint(user_bp, url_prefix='/user')
    
    from app.search import bp as search_bp
    app.register_blueprint(search_bp, url_prefix='/search')
    
    from app.message import bp as message_bp
    app.register_blueprint(message_bp, url_prefix='/message')
    
    from app.lease import bp as lease_bp
    app.register_blueprint(lease_bp, url_prefix='/lease')
    
    from app.repair import bp as repair_bp
    app.register_blueprint(repair_bp, url_prefix='/repair')
    
    from app.stats import bp as stats_bp
    app.register_blueprint(stats_bp, url_prefix='/stats')
    
    from app.monitor import bp as monitor_bp
    app.register_blueprint(monitor_bp, url_prefix='/monitor')
    
    from app.regions import bp as regions_bp
    app.register_blueprint(regions_bp, url_prefix='/api/regions')

    from app.news import bp as news_bp
    app.register_blueprint(news_bp, url_prefix='/news')

    from app.complaint import bp as complaint_bp
    app.register_blueprint(complaint_bp, url_prefix='/complaint')

    # 注册错误处理
    register_error_handlers(app)

    # 注册 Jinja2 过滤器
    @app.template_filter('load_json')
    def load_json(s):
        try:
            return json.loads(s)
        except (ValueError, TypeError):
            return []

    # 自动初始化数据库
    with app.app_context():
        try:
            db.create_all()
            create_admin_user()
        except Exception as e:
            print(f'数据库初始化警告: {e}')

    return app


@login_manager.user_loader
def load_user(user_id):
    """加载用户"""
    from app.models import User
    return User.query.get(int(user_id))


def register_error_handlers(app):
    """注册错误处理器"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500


def create_admin_user():
    """创建默认管理员账户"""
    from app.models import User
    
    admin_email = Config.ADMIN_EMAIL
    if not User.query.filter_by(email=admin_email).first():
        admin = User(
            username='admin',
            email=admin_email,
            password_hash='',  # 会在set_password中设置
            role='admin',
            status='active'
        )
        admin.set_password(Config.ADMIN_PASSWORD)
        db.session.add(admin)
        db.session.commit()
        print(f'管理员账户已创建: {admin_email}')
