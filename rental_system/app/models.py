from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


class User(UserMixin, db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), nullable=False, default='tenant')  # landlord/tenant/admin
    real_name = db.Column(db.String(100))
    id_card = db.Column(db.String(18))
    avatar = db.Column(db.String(256))
    status = db.Column(db.String(20), default='active')  # active/inactive/banned
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # 关系
    houses = db.relationship('House', backref='landlord', lazy='dynamic')
    leases_as_tenant = db.relationship('LeaseContract', backref='tenant', lazy='dynamic', 
                                       foreign_keys='LeaseContract.tenant_id')
    leases_as_landlord = db.relationship('LeaseContract', backref='landlord', lazy='dynamic',
                                         foreign_keys='LeaseContract.landlord_id')
    appointments_as_tenant = db.relationship('Appointment', backref='tenant', lazy='dynamic',
                                             foreign_keys='Appointment.tenant_id')
    appointments_as_landlord = db.relationship('Appointment', backref='landlord', lazy='dynamic',
                                               foreign_keys='Appointment.landlord_id')
    messages_sent = db.relationship('Message', backref='sender', lazy='dynamic', 
                                    foreign_keys='Message.sender_id')
    messages_received = db.relationship('Message', backref='receiver', lazy='dynamic',
                                        foreign_keys='Message.receiver_id')
    repair_requests = db.relationship('RepairRequest', backref='tenant', lazy='dynamic')
    complaints = db.relationship('Complaint', backref='tenant', lazy='dynamic')
    activities = db.relationship('UserActivity', backref='user', lazy='dynamic')
    logs = db.relationship('SystemLog', backref='user', lazy='dynamic')
    news_articles = db.relationship('News', backref='publisher', lazy='dynamic')
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """是否为管理员"""
        return self.role == 'admin'
    
    def is_landlord(self):
        """是否为房东"""
        return self.role == 'landlord'
    
    def is_tenant(self):
        """是否为租客"""
        return self.role == 'tenant'
    
    def __repr__(self):
        return f'<User {self.username}>'


class Region(db.Model):
    """行政区划模型（省/市/区）"""
    __tablename__ = 'regions'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)  # 行政区划代码
    name = db.Column(db.String(100), nullable=False)  # 名称
    parent_code = db.Column(db.String(20), index=True)  # 父级代码（省为空，市为省代码，区为市代码）
    level = db.Column(db.Integer, nullable=False)  # 级别：1-省/直辖市/自治区，2-市/区，3-县/区
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<Region {self.name}>'
    
    @staticmethod
    def get_provinces():
        """获取所有省份"""
        return Region.query.filter_by(level=1, is_active=True).order_by(Region.code).all()
    
    @staticmethod
    def get_cities(province_code):
        """获取指定省份下的所有城市"""
        return Region.query.filter_by(parent_code=province_code, level=2, is_active=True).order_by(Region.code).all()
    
    @staticmethod
    def get_districts(city_code):
        """获取指定城市下的所有区县"""
        return Region.query.filter_by(parent_code=city_code, level=3, is_active=True).order_by(Region.code).all()
    
    @staticmethod
    def get_by_code(code):
        """根据代码获取地区"""
        return Region.query.filter_by(code=code, is_active=True).first()
    
    @staticmethod
    def search_by_name(name, level=None):
        """根据名称搜索地区"""
        query = Region.query.filter(Region.name.like(f'%{name}%'), Region.is_active == True)
        if level:
            query = query.filter_by(level=level)
        return query.order_by(Region.level, Region.code).all()


class House(db.Model):
    """房源模型"""
    __tablename__ = 'houses'
    
    id = db.Column(db.Integer, primary_key=True)
    landlord_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(300), nullable=False)
    district = db.Column(db.String(100), nullable=False, index=True)  # 区域 - 添加索引
    area = db.Column(db.String(100))  # 所属区域/商圈
    type = db.Column(db.String(50))  # 房屋类型：公寓/住宅/别墅等
    room_count = db.Column(db.String(20), index=True)  # 几室几厅，如"3室2厅" - 添加索引
    size = db.Column(db.Float)  # 面积（平方米）
    rent_price = db.Column(db.Float, nullable=False, index=True)  # 租金 - 添加索引
    deposit = db.Column(db.Float, default=0)  # 押金
    decoration = db.Column(db.String(50))  # 装修情况：精装/简装/毛坯
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='available')  # available/rented/maintenance
    lat = db.Column(db.Float)  # 纬度
    lng = db.Column(db.Float)  # 经度
    province_code = db.Column(db.String(20))  # 省份代码
    city_code = db.Column(db.String(20))  # 城市代码
    district_code = db.Column(db.String(20))  # 区县代码
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                          onupdate=lambda: datetime.now(timezone.utc))
    
    # 关系
    media = db.relationship('HouseMedia', backref='house', lazy='dynamic', 
                           cascade='all, delete-orphan')
    contracts = db.relationship('LeaseContract', backref='house', lazy='dynamic')
    appointments = db.relationship('Appointment', backref='house', lazy='dynamic')
    repair_requests = db.relationship('RepairRequest', backref='house', lazy='dynamic')
    complaints = db.relationship('Complaint', backref='house', lazy='dynamic')
    
    def get_images(self):
        """获取所有图片"""
        return HouseMedia.query.filter_by(house_id=self.id, media_type='image').order_by(
            HouseMedia.order).all()
    
    def get_images_list(self):
        """获取图片路径列表"""
        images = self.get_images()
        return [img.url for img in images]
    
    def get_videos(self):
        """获取所有视频"""
        return HouseMedia.query.filter_by(house_id=self.id, media_type='video').order_by(
            HouseMedia.order).all()
    
    def __repr__(self):
        return f'<House {self.title}>'


class HouseMedia(db.Model):
    """房源媒体文件（图片/视频）"""
    __tablename__ = 'house_media'
    
    id = db.Column(db.Integer, primary_key=True)
    house_id = db.Column(db.Integer, db.ForeignKey('houses.id'), nullable=False, index=True)
    media_type = db.Column(db.String(20), nullable=False)  # image/video
    url = db.Column(db.String(500), nullable=False)
    order = db.Column(db.Integer, default=0)  # 排序
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<HouseMedia {self.id}>'


class LeaseContract(db.Model):
    """租赁合同"""
    __tablename__ = 'lease_contracts'
    
    id = db.Column(db.Integer, primary_key=True)
    house_id = db.Column(db.Integer, db.ForeignKey('houses.id'), nullable=False, index=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    landlord_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    rent_amount = db.Column(db.Float, nullable=False)
    deposit_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50))  # monthly/quarterly/etc
    status = db.Column(db.String(20), default='pending')  # pending/active/terminated/rejected
    signed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # 关系
    payments = db.relationship('RentPayment', backref='contract', lazy='dynamic',
                              cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<LeaseContract {self.id}>'


class Appointment(db.Model):
    """看房预约"""
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    house_id = db.Column(db.Integer, db.ForeignKey('houses.id'), nullable=False, index=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    landlord_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    appointment_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending/confirmed/cancelled/completed
    remark = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<Appointment {self.id}>'


class RentPayment(db.Model):
    """租金支付记录"""
    __tablename__ = 'rent_payments'
    
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('lease_contracts.id'), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.Date)  # 账单周期起始日期
    end_date = db.Column(db.Date)  # 账单周期截止日期
    due_date = db.Column(db.Date, nullable=False)  # 付款到期日
    paid_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='unpaid')  # unpaid/paid/overdue
    payment_method = db.Column(db.String(50))  # alipay/wechat/bank
    transaction_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<RentPayment {self.id}>'


class Message(db.Model):
    """消息"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default='message')  # message/notification
    read_status = db.Column(db.Boolean, default=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('messages.id'))  # 回复的消息ID
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    # 自引用关系
    replies = db.relationship('Message', backref=db.backref('parent', remote_side=[id]),
                             lazy='dynamic', foreign_keys=[parent_id])
    
    def __repr__(self):
        return f'<Message {self.id}>'


class News(db.Model):
    """新闻公告"""
    __tablename__ = 'news'
    
    id = db.Column(db.Integer, primary_key=True)
    publisher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))
    status = db.Column(db.String(20), default='draft')  # draft/published/archived
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    published_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<News {self.title}>'


class RepairRequest(db.Model):
    """维修申请"""
    __tablename__ = 'repair_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    house_id = db.Column(db.Integer, db.ForeignKey('houses.id'), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending/processing/completed/rejected
    images = db.Column(db.Text)  # JSON格式存储图片路径
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    resolved_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<RepairRequest {self.id}>'


class Complaint(db.Model):
    """投诉"""
    __tablename__ = 'complaints'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    house_id = db.Column(db.Integer, db.ForeignKey('houses.id'), nullable=False, index=True)
    target_type = db.Column(db.String(50))  # 投诉对象类型：landlord/house/service
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending/processing/resolved/rejected
    response = db.Column(db.Text)  # 处理回复
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    resolved_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Complaint {self.id}>'


class SystemLog(db.Model):
    """系统日志"""
    __tablename__ = 'system_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    action = db.Column(db.String(100), nullable=False)
    ip = db.Column(db.String(50))
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    def __repr__(self):
        return f'<SystemLog {self.action}>'


class UserActivity(db.Model):
    """用户活动记录"""
    __tablename__ = 'user_activities'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    action_type = db.Column(db.String(50), nullable=False)  # login/view_house/book/etc
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    details = db.Column(db.Text)  # JSON格式的详细信息
    
    def __repr__(self):
        return f'<UserActivity {self.action_type}>'


# Flask-Login用户加载函数
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
