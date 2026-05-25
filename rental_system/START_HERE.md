# 快速启动指南 🚀

## 项目已准备就绪！✅

所有核心文件和数据库模型已按照您的要求创建完成。

## 第一步：安装依赖

```bash
cd D:\PyCharmProject\rental_system
pip install -r requirements.txt
```

## 第二步：初始化数据库

```bash
# Windows PowerShell
$env:FLASK_APP="run.py"
flask db init
flask db migrate -m "initial migration"
flask db upgrade
```

或者使用CMD：
```cmd
set FLASK_APP=run.py
flask db init
flask db migrate -m "initial migration"
flask db upgrade
```

## 第三步：运行应用

```bash
python run.py
```

访问 http://localhost:5000

## 默认管理员账户

- **邮箱**: admin@rentalsystem.com
- **密码**: admin123

## 数据库模型概览（12个）

### 核心模型
1. **User** - 用户（含real_name, id_card, status字段）
2. **House** - 房源（含lat, lng, room_count, district索引）
3. **HouseMedia** - 媒体文件（图片/视频）
4. **LeaseContract** - 租赁合同
5. **Appointment** - 看房预约
6. **RentPayment** - 租金支付
7. **Message** - 消息（支持回复）
8. **News** - 新闻公告
9. **RepairRequest** - 维修申请
10. **Complaint** - 投诉
11. **SystemLog** - 系统日志
12. **UserActivity** - 用户活动

### 关键索引
- ✅ House.district (区域搜索)
- ✅ House.room_count (户型筛选)
- ✅ House.rent_price (价格排序)
- ✅ 所有外键字段都有索引

## 需要完善的内容

### 高优先级（必须）
1. **app/forms.py** - 添加表单类定义
   ```python
   from flask_wtf import FlaskForm
   from wtforms import StringField, PasswordField, EmailField, FloatField
   from wtforms.validators import DataRequired, Email, Length
   
   class LoginForm(FlaskForm):
       email = EmailField('邮箱', validators=[DataRequired(), Email()])
       password = PasswordField('密码', validators=[DataRequired()])
       submit = SubmitField('登录')
   ```

2. **app/auth/views.py** - 实现登录注册
3. **app/house/views.py** - 实现房源CRUD

### 中优先级
4. 完善其他模块的views.py
5. 完善HTML模板内容
6. 添加文件上传功能

### 低优先级
7. 统计和监控功能
8. 高级搜索算法
9. 性能优化

## 常用命令

```bash
# 进入Flask Shell
flask shell

# 查看数据库模型
>>> from app.models import User, House
>>> User.query.all()

# 创建新用户
>>> user = User(username='test', email='test@test.com', role='tenant')
>>> user.set_password('password123')
>>> db.session.add(user)
>>> db.session.commit()

# 数据库迁移
flask db migrate -m "描述变更"
flask db upgrade
```

## 项目文件统计

- Python文件: 26个
- HTML模板: 21个
- 数据库模型: 12个
- 蓝图模块: 9个
- 总代码量: 约500+行（框架）

## 下一步建议

1. **先测试基础功能**
   - 运行应用，确保能正常启动
   - 测试管理员登录
   
2. **完善认证模块**
   - 实现完整的登录/注册逻辑
   - 添加表单验证

3. **实现房源管理**
   - 发布房源
   - 浏览房源
   - 搜索房源

4. **逐步扩展**
   - 租赁功能
   - 消息系统
   - 维修服务

## 技术文档

- `REBUILD_SUMMARY.md` - 重建总结
- `FILE_CREATION_GUIDE.md` - 文件创建指南
- `README.md` - 项目说明
- `QUICKSTART.md` - 快速参考

## 遇到问题？

### 数据库错误
```bash
# 删除数据库重新初始化
rm instance/rental_system.db
flask db upgrade
```

### 导入错误
```bash
# 确保在正确的目录
cd D:\PyCharmProject\rental_system
# 检查Python路径
python -c "import sys; print(sys.path)"
```

### 模块找不到
```bash
# 安装缺失的包
pip install flask-wtf flask-login flask-sqlalchemy flask-mail flask-migrate
```

---

**祝您开发顺利！** 🎉

如有问题，请查看详细文档或检查代码注释。
