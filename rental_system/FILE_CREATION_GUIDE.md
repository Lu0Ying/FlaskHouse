# 项目文件创建指南

## 已完成的核心文件 ✅

### 配置文件
- [x] `.env` - 环境变量
- [x] `config.py` - 配置类
- [x] `run.py` - 启动入口
- [x] `requirements.txt` - 依赖清单

### 核心应用
- [x] `app/__init__.py` - 应用工厂
- [x] `app/models.py` - **新数据库模型（12个）**
- [x] `app/utils/__init__.py`
- [x] `app/utils/security.py` - 密码加密
- [x] `app/utils/file_upload.py` - 文件上传

### 蓝图初始化
- [x] `app/auth/__init__.py`
- [x] `app/house/__init__.py`
- [x] `app/user/__init__.py`
- [x] `app/search/__init__.py`
- [x] `app/message/__init__.py`
- [x] `app/lease/__init__.py`
- [x] `app/repair/__init__.py`
- [x] `app/stats/__init__.py`
- [x] `app/monitor/__init__.py`

## 需要补充的文件 📝

### 1. 表单定义 (app/forms.py)

创建 `app/forms.py`，包含以下表单类：

```python
from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import *
from app.models import User

class LoginForm(FlaskForm):
    email = EmailField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')

class RegistrationForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=3, max=64)])
    email = EmailField('邮箱', validators=[DataRequired(), Email()])
    phone = StringField('手机号')
    real_name = StringField('真实姓名')
    id_card = StringField('身份证号')
    password = PasswordField('密码', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('角色', choices=[('tenant', '租客'), ('landlord', '房东')])
    submit = SubmitField('注册')
    
    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已存在')
    
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱已被注册')

class HouseForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired()])
    address = StringField('地址', validators=[DataRequired()])
    district = StringField('区域', validators=[DataRequired()])
    area = StringField('商圈')
    type = SelectField('房屋类型', choices=[('公寓', '公寓'), ('住宅', '住宅'), ('别墅', '别墅')])
    room_count = StringField('户型（如3室2厅）', validators=[DataRequired()])
    size = FloatField('面积（㎡）')
    rent_price = FloatField('租金（元/月）', validators=[DataRequired()])
    deposit = FloatField('押金')
    decoration = SelectField('装修', choices=[('精装', '精装'), ('简装', '简装'), ('毛坯', '毛坯')])
    description = TextAreaField('描述')
    lat = FloatField('纬度')
    lng = FloatField('经度')
    images = FileField('图片', render_kw={'multiple': True})
    videos = FileField('视频', render_kw={'multiple': True})
    submit = SubmitField('提交')

# ... 其他表单类
```

### 2. 工具函数补充

**app/utils/email.py** - 邮件发送：
```python
from flask_mail import Message
from app import mail
import threading

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipients, text_body, html_body=None):
    msg = Message(subject, recipients=[recipients] if isinstance(recipients, str) else recipients)
    msg.body = text_body
    if html_body:
        msg.html = html_body
    
    from flask import current_app
    app = current_app._get_current_object()
    thread = threading.Thread(target=send_async_email, args=(app, msg))
    thread.start()
```

**app/utils/contract.py** - PDF合同生成（可选）：
```python
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def generate_contract_pdf(contract, output_path):
    c = canvas.Canvas(output_path, pagesize=A4)
    c.drawString(100, 750, f"租赁合同 #{contract.id}")
    c.drawString(100, 730, f"租客: {contract.tenant.real_name}")
    c.drawString(100, 710, f"租期: {contract.start_date} 至 {contract.end_date}")
    c.save()
```

### 3. 视图文件（每个蓝图模块）

每个模块需要创建 `views.py` 文件，例如：

**app/auth/views.py**:
```python
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.auth import bp
from app.models import User, SystemLog
from app.forms import LoginForm, RegistrationForm
from app.utils.security import hash_password

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('house.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('邮箱或密码错误', 'danger')
            return redirect(url_for('auth.login'))
        
        if user.status != 'active':
            flash('账户已被禁用', 'danger')
            return redirect(url_for('auth.login'))
        
        login_user(user)
        
        # 记录日志
        log = SystemLog(user_id=user.id, action='login', ip=request.remote_addr)
        db.session.add(log)
        db.session.commit()
        
        next_page = request.args.get('next')
        return redirect(next_page or url_for('house.index'))
    
    return render_template('auth/login.html', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('house.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            phone=form.phone.data,
            real_name=form.real_name.data,
            id_card=form.id_card.data,
            role=form.role.data,
            status='active'
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功！请登录', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
```

**app/house/views.py** (关键路由示例):
```python
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.house import bp
from app.models import House, HouseMedia
from app.forms import HouseForm
from app.utils.file_upload import save_multiple_files

@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    houses = House.query.filter_by(status='available').order_by(
        House.created_at.desc()
    ).paginate(page=page, per_page=10)
    return render_template('house/index.html', houses=houses)

@bp.route('/<int:id>')
def detail(id):
    house = House.query.get_or_404(id)
    return render_template('house/detail.html', house=house)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.is_landlord():
        flash('只有房东可以发布房源', 'danger')
        return redirect(url_for('house.index'))
    
    form = HouseForm()
    if form.validate_on_submit():
        house = House(
            landlord_id=current_user.id,
            title=form.title.data,
            address=form.address.data,
            district=form.district.data,
            area=form.area.data,
            type=form.type.data,
            room_count=form.room_count.data,
            size=form.size.data,
            rent_price=form.rent_price.data,
            deposit=form.deposit.data,
            decoration=form.decoration.data,
            description=form.description.data,
            lat=form.lat.data,
            lng=form.lng.data,
            status='available'
        )
        
        db.session.add(house)
        db.session.flush()  # 获取house.id
        
        # 保存图片
        images = request.files.getlist('images')
        for idx, img in enumerate(images):
            if img and img.filename:
                from app.utils.file_upload import save_upload_file
                path = save_upload_file(img, 'uploads/houses')
                if path:
                    media = HouseMedia(
                        house_id=house.id,
                        media_type='image',
                        url=path,
                        order=idx
                    )
                    db.session.add(media)
        
        db.session.commit()
        flash('房源发布成功', 'success')
        return redirect(url_for('house.detail', id=house.id))
    
    return render_template('house/create.html', form=form)
```

### 4. 模板文件

需要创建的模板目录结构：
```
app/templates/
├── base.html
├── auth/
│   ├── login.html
│   └── register.html
├── house/
│   ├── index.html
│   ├── detail.html
│   ├── create.html
│   └── edit.html
├── user/
│   ├── profile.html
│   └── my_houses.html
├── search/
│   └── search.html
├── message/
│   ├── inbox.html
│   └── send.html
├── lease/
│   ├── contracts.html
│   └── appointments.html
├── repair/
│   ├── create.html
│   └── list.html
├── stats/
│   └── dashboard.html
├── monitor/
│   ├── logs.html
│   └── users.html
└── errors/
    ├── 404.html
    └── 500.html
```

**base.html 示例**:
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{% block title %}{% endblock %} - 智能房屋租赁系统</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('house.index') }}">房屋租赁系统</a>
            <div class="navbar-nav">
                {% if current_user.is_authenticated %}
                    <a class="nav-link" href="{{ url_for('user.profile') }}">{{ current_user.username }}</a>
                    <a class="nav-link" href="{{ url_for('auth.logout') }}">退出</a>
                {% else %}
                    <a class="nav-link" href="{{ url_for('auth.login') }}">登录</a>
                    <a class="nav-link" href="{{ url_for('auth.register') }}">注册</a>
                {% endif %}
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </div>
</body>
</html>
```

### 5. 快速创建剩余文件的脚本

创建一个Python脚本 `generate_files.py` 来批量生成空文件：

```python
import os

# 定义需要创建的文件列表
files = [
    'app/forms.py',
    'app/utils/email.py',
    'app/utils/contract.py',
    'app/auth/views.py',
    'app/house/views.py',
    'app/user/views.py',
    'app/search/views.py',
    'app/message/views.py',
    'app/lease/views.py',
    'app/repair/views.py',
    'app/stats/views.py',
    'app/monitor/views.py',
]

templates = [
    'app/templates/base.html',
    'app/templates/auth/login.html',
    'app/templates/auth/register.html',
    'app/templates/house/index.html',
    'app/templates/house/detail.html',
    'app/templates/errors/404.html',
    'app/templates/errors/500.html',
]

for file in files + templates:
    path = os.path.join('D:\\PyCharmProject\\rental_system', file)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            if file.endswith('.py'):
                f.write('# TODO: Implement this module\n')
            elif file.endswith('.html'):
                f.write('{% extends "base.html" %}\n{% block content %}\n{% endblock %}\n')
        print(f'Created: {file}')

print('All files created!')
```

## 新数据库模型说明 📊

### 核心变化
1. **User模型**：新增 `real_name`, `id_card`, `status` 字段
2. **House模型**：新增 `lat`, `lng`, `area`, `type`, `room_count`, `size`, `decoration`
3. **HouseMedia**：独立的媒体表，支持多图片/视频
4. **Appointment**：看房预约，关联房东和租客
5. **UserActivity**：用户活动追踪
6. **索引优化**：district, room_count, rent_price 添加索引

### 外键关系
- House → User (landlord_id)
- HouseMedia → House (house_id)
- LeaseContract → House, User (tenant/landlord)
- Appointment → House, User (tenant/landlord)
- RentPayment → LeaseContract
- Message → User (sender/receiver)
- RepairRequest → User, House
- Complaint → User, House
- SystemLog → User
- UserActivity → User

## 运行步骤 🚀

```bash
cd D:\PyCharmProject\rental_system

# 1. 安装依赖
pip install -r requirements.txt

# 2. 初始化数据库
flask db init
flask db migrate -m "initial"
flask db upgrade

# 3. 运行
python run.py
```

访问 http://localhost:5000

默认管理员：
- 邮箱: admin@rentalsystem.com
- 密码: admin123

## 下一步建议 💡

1. 先创建 `app/forms.py` 和各个 `views.py`
2. 然后创建基础模板 `base.html` 和登录/注册页面
3. 实现核心的房源发布和浏览功能
4. 逐步完善其他模块

所有代码都已按照您的新模型定义进行了调整！
