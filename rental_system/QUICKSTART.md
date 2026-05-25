# 快速参考指南

## 常用命令

### 开发环境
```bash
# 启动应用
python run.py

# Flask Shell
flask shell

# 数据库迁移
flask db migrate -m "描述"
flask db upgrade

# 运行测试
pytest tests/ -v
```

### 生产环境
```bash
# 使用Gunicorn启动
gunicorn -w 4 -b 127.0.0.1:8000 run:app

# Supervisor管理
sudo supervisorctl status rental_system
sudo supervisorctl restart rental_system
sudo supervisorctl tail rental_system stderr
```

## 默认账户

**管理员**:
- 邮箱: admin@rentalsystem.com
- 密码: admin123

## API端点速查

### 公开API
```
GET  /house/api/search?keyword=test&city=北京
GET  /monitor/health
```

### 需要认证
```
GET  /message/api/unread-count
```

## 用户角色权限

| 功能 | 租客 | 房东 | 管理员 |
|------|------|------|--------|
| 浏览房源 | ✅ | ✅ | ✅ |
| 发布房源 | ❌ | ✅ | ✅ |
| 预约看房 | ✅ | ❌ | ✅ |
| 创建合同 | ✅ | ❌ | ✅ |
| 签署合同 | ✅ | ✅ | ✅ |
| 查看统计 | ❌ | ❌ | ✅ |
| 系统监控 | ❌ | ❌ | ✅ |
| 用户管理 | ❌ | ❌ | ✅ |

## 房源状态

- `available` - 可租
- `rented` - 已租
- `maintenance` - 维护中

## 合同状态

- `pending` - 待签署
- `active` - 生效中
- `expired` - 已到期
- `terminated` - 已终止

## 维修状态

- `pending` - 待处理
- `in_progress` - 处理中
- `completed` - 已完成
- `rejected` - 已拒绝

## 常见问题

### Q1: 如何重置管理员密码？
```python
flask shell
>>> from app.models import User
>>> from app.utils.security import hash_password
>>> user = User.query.filter_by(email='admin@rentalsystem.com').first()
>>> user.password_hash = hash_password('newpassword')
>>> db.session.commit()
```

### Q2: 如何添加测试数据？
```python
flask shell
>>> from app.models import User, House
>>> from app import db
>>> # 创建测试用户
>>> user = User(username='test', email='test@test.com', role='landlord')
>>> user.set_password('test123')
>>> db.session.add(user)
>>> db.session.commit()
```

### Q3: 如何备份数据库？
```bash
# SQLite
cp instance/rental_system.db backup.db

# PostgreSQL
pg_dump rental_db > backup.sql

# MySQL
mysqldump rental_db > backup.sql
```

### Q4: 如何查看日志？
```bash
# 应用日志
tail -f logs/error.log

# Nginx日志
tail -f /var/log/nginx/access.log

# Supervisor日志
sudo supervisorctl tail rental_system stderr
```

### Q5: 上传文件存储位置？
```
app/static/uploads/
├── houses/      # 房源图片/视频
├── avatars/     # 用户头像
├── contracts/   # PDF合同
└── repairs/     # 维修图片
```

## 环境变量速查

```env
# 必需配置
SECRET_KEY=随机字符串
DATABASE_URL=sqlite:///rental_system.db

# 邮件配置（可选）
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-password

# 文件上传
UPLOAD_FOLDER=app/static/uploads
MAX_CONTENT_LENGTH=16777216  # 16MB
```

## 数据库表关系

```
User (用户)
├── houses (发布的房源)
├── leases (作为租客的合同)
├── landlord_contracts (作为房东的合同)
├── messages_sent (发送的消息)
├── messages_received (接收的消息)
├── repairs (维修申请)
├── complaints (投诉)
└── viewings (看房预约)

House (房源)
├── contracts (相关合同)
├── viewing_appointments (看房预约)
└── repairs (维修记录)

LeaseContract (合同)
└── payments (支付记录)
```

## 表单验证规则

### 密码要求
- 最小长度: 8字符
- 必须包含字母和数字

### 文件上传限制
- 最大大小: 16MB
- 允许格式: jpg, jpeg, png, gif, mp4

### 邮箱验证
- 必须符合邮箱格式
- 注册后发送验证链接

## 性能优化建议

### 数据库索引
已添加索引的字段:
- User: username, email
- House: district, city, owner_id
- LeaseContract: contract_number
- SystemLog: created_at

### 缓存策略
```python
# 推荐安装 Flask-Caching
pip install Flask-Caching

# 配置Redis缓存
CACHE_TYPE = 'redis'
CACHE_REDIS_URL = 'redis://localhost:6379/0'
```

### 分页设置
```python
ITEMS_PER_PAGE = 10  # 每页显示数量
```

## 安全清单

部署前检查:
- [ ] 修改SECRET_KEY
- [ ] 更改管理员密码
- [ ] 配置HTTPS
- [ ] 设置防火墙
- [ ] 启用数据库备份
- [ ] 配置日志轮转
- [ ] 限制文件上传大小
- [ ] 启用CSRF保护
- [ ] 配置CORS策略
- [ ] 隐藏调试信息

## 调试技巧

### 启用调试模式
```python
# .env
FLASK_ENV=development
FLASK_DEBUG=1
```

### 查看SQL查询
```python
# app/__init__.py
app.config['SQLALCHEMY_ECHO'] = True
```

### Flask Shell快捷方式
```python
# run.py
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'House': House}
```

使用:
```bash
flask shell
>>> User.query.all()
>>> House.query.filter_by(status='available').count()
```

## 扩展包推荐

### 已使用
- Flask-SQLAlchemy - ORM
- Flask-Login - 认证
- Flask-WTF - 表单
- Flask-Migrate - 迁移
- Flask-Mail - 邮件
- bcrypt - 密码加密
- pyotp - 双因素认证
- reportlab - PDF生成

### 推荐添加
- Flask-Caching - 缓存
- Flask-RESTful - REST API
- Flask-Limiter - 限流
- Flask-Talisman - 安全头
- Celery - 异步任务
- Redis - 缓存/队列

---

**更多详细信息请查看**:
- README.md - 完整说明
- PROJECT_SUMMARY.md - 项目总结
- DEPLOYMENT.md - 部署指南
- STRUCTURE.md - 项目结构
