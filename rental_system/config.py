import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """应用配置类"""
    
    # Flask 核心配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    
    # 数据库配置 - 使用 MySQL 数据库
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@localhost/rental_system'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 邮件配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@rentalsystem.com'
    
    # 文件上传配置
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'app/static/uploads'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH') or 16 * 1024 * 1024)  # 16MB
    ALLOWED_EXTENSIONS = set(os.environ.get('ALLOWED_EXTENSIONS', 'jpg,jpeg,png,gif,mp4').split(','))
    
    # 分页配置
    ITEMS_PER_PAGE = int(os.environ.get('ITEMS_PER_PAGE') or 10)
    
    # 管理员配置
    ADMIN_EMAIL = 'admin@rentalsystem.com'
    ADMIN_PASSWORD = 'admin123'  # 首次运行时自动创建
