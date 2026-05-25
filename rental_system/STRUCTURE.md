# 项目结构详细说明

## 完整目录树

```
rental_system/
│
├── .env                          # 环境变量配置文件
├── .gitignore                    # Git忽略配置
├── requirements.txt              # Python依赖包列表
├── run.py                        # 应用启动入口
├── config.py                     # 配置类定义
├── start.bat                     # Windows快速启动脚本
├── README.md                     # 项目说明文档
├── PROJECT_SUMMARY.md            # 项目总结文档
├── DEPLOYMENT.md                 # 部署指南
│
├── app/                          # 主应用包
│   ├── __init__.py              # 应用工厂、扩展初始化
│   ├── models.py                # 数据库模型（10个模型类）
│   ├── forms.py                 # WTForms表单（15个表单类）
│   │
│   ├── utils/                   # 工具函数模块
│   │   ├── __init__.py
│   │   ├── security.py          # 密码加密、双因素认证
│   │   ├── email.py             # 邮件发送功能
│   │   ├── file_upload.py       # 文件上传处理
│   │   └── contract.py          # PDF合同生成
│   │
│   ├── auth/                    # 认证模块（蓝图）
│   │   ├── __init__.py
│   │   └── views.py             # 登录、注册、2FA等视图
│   │
│   ├── house/                   # 房源管理模块（蓝图）
│   │   ├── __init__.py
│   │   └── views.py             # 房源CRUD、状态管理等
│   │
│   ├── user/                    # 用户管理模块（蓝图）
│   │   ├── __init__.py
│   │   └── views.py             # 个人资料、我的合同等
│   │
│   ├── search/                  # 智能搜索模块（蓝图）
│   │   ├── __init__.py
│   │   └── views.py             # 多条件搜索、智能推荐
│   │
│   ├── message/                 # 消息与新闻模块（蓝图）
│   │   ├── __init__.py
│   │   └── views.py             # 消息收发、新闻管理
│   │
│   ├── lease/                   # 租赁管理模块（蓝图）
│   │   ├── __init__.py
│   │   └── views.py             # 预约看房、合同签署、支付
│   │
│   ├── repair/                  # 维修与投诉模块（蓝图）
│   │   ├── __init__.py
│   │   └── views.py             # 维修申请、投诉处理
│   │
│   ├── stats/                   # 报表统计模块（蓝图）
│   │   ├── __init__.py
│   │   └── views.py             # 数据统计、图表展示
│   │
│   ├── monitor/                 # 系统监控模块（蓝图）
│   │   ├── __init__.py
│   │   └── views.py             # 日志查看、用户管理
│   │
│   ├── templates/               # Jinja2模板目录
│   │   ├── base.html            # 基础模板
│   │   │
│   │   ├── auth/                # 认证相关模板
│   │   │   ├── login.html
│   │   │   ├── register.html
│   │   │   └── two_factor.html
│   │   │
│   │   ├── house/               # 房源相关模板
│   │   │   └── index.html
│   │   │
│   │   └── errors/              # 错误页面
│   │       ├── 404.html
│   │       └── 500.html
│   │
│   └── static/                  # 静态资源目录
│       ├── css/                 # CSS文件
│       ├── js/                  # JavaScript文件
│       └── uploads/             # 上传文件存储
│           ├── houses/          # 房源图片/视频
│           ├── avatars/         # 用户头像
│           ├── contracts/       # PDF合同
│           └── repairs/         # 维修图片
│
└── tests/                       # 测试目录
    ├── test_auth.py             # 认证模块测试
    ├── test_house.py            # 房源模块测试（待创建）
    └── test_api.py              # API测试（待创建）
```

## 核心文件说明

### 1. 配置文件

#### `.env` - 环境变量
```env
FLASK_APP=run.py
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///rental_system.db
MAIL_SERVER=smtp.gmail.com
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-password
UPLOAD_FOLDER=app/static/uploads
MAX_CONTENT_LENGTH=16777216
ITEMS_PER_PAGE=10
```

#### `config.py` - 配置类
- 从`.env`读取配置
- 提供默认值
- 支持不同环境（开发/测试/生产）

### 2. 应用核心

#### `app/__init__.py` - 应用工厂
**主要功能**:
- `create_app()` - 创建Flask应用实例
- 初始化扩展（db, login_manager, migrate, mail）
- 注册8个蓝图
- 注册错误处理器
- 创建默认管理员账户
- `load_user()` - Flask-Login用户加载回调

#### `app/models.py` - 数据库模型
**包含10个模型类**:
1. **User** - 用户模型
   - 基本信息：用户名、邮箱、密码哈希
   - 角色：tenant/landlord/admin
   - 双因素认证支持
   - 关系：houses, leases, messages等

2. **House** - 房源模型
   - 基本信息：标题、地址、价格、面积
   - 户型：室、厅、卫
   - 设施：精装、电梯
   - 状态：available/rented/maintenance
   - 媒体：图片列表、视频

3. **LeaseContract** - 租赁合同
   - 合同编号、租期、租金
   - 签署状态跟踪
   - PDF合同路径

4. **RentPayment** - 租金支付记录
   - 金额、日期、支付方式
   - 状态：pending/paid/overdue

5. **ViewingAppointment** - 看房预约
   - 预约时间、状态
   - 备注信息

6. **Message** - 消息
   - 发送者、接收者
   - 主题、内容
   - 已读状态、回复关系

7. **News** - 新闻公告
   - 标题、内容、分类
   - 发布状态、浏览量

8. **RepairRequest** - 维修申请
   - 问题描述、优先级
   - 状态跟踪、指派人

9. **Complaint** - 投诉
   - 投诉类别、状态
   - 官方回复

10. **SystemLog** - 系统日志
    - 操作类型、IP地址
    - 日志级别、时间戳

#### `app/forms.py` - 表单定义
**包含15个表单类**:
- LoginForm, RegistrationForm - 认证表单
- ProfileUpdateForm - 个人资料
- HouseForm - 房源发布
- SearchForm - 搜索筛选
- MessageForm, NewsForm - 消息和新闻
- ViewingAppointmentForm - 看房预约
- LeaseContractForm - 合同创建
- RentPaymentForm - 租金支付
- RepairRequestForm, ComplaintForm - 维修和投诉
- TwoFactorForm - 双因素验证

### 3. 工具模块

#### `app/utils/security.py`
```python
hash_password(password)           # bcrypt加密
verify_password(password, hash)   # 密码验证
generate_two_factor_secret()      # 生成2FA密钥
generate_two_factor_token(secret) # 生成TOTP验证码
verify_two_factor_token(secret, token) # 验证2FA
```

#### `app/utils/email.py`
```python
send_email(subject, recipients, text_body, html_body)  # 通用发送
send_verification_email(user)     # 验证邮件
send_password_reset_email(user)   # 密码重置
send_notification_email(user, subject, message)  # 通知邮件
```

#### `app/utils/file_upload.py`
```python
allowed_file(filename)            # 检查文件类型
save_upload_file(file, subfolder) # 保存单个文件
save_multiple_files(files, subfolder) # 保存多个文件
delete_file(filepath)             # 删除文件
```

#### `app/utils/contract.py`
```python
generate_contract_pdf(contract, output_path)  # 生成PDF合同
```

### 4. 蓝图模块

每个蓝图模块包含：
- `__init__.py` - 创建Blueprint对象
- `views.py` - 路由视图函数

#### 路由概览

**auth/** (认证)
- `/auth/login` - 登录
- `/auth/register` - 注册
- `/auth/logout` - 登出
- `/auth/two-factor-verify` - 2FA验证
- `/auth/enable-2fa` - 启用2FA
- `/auth/disable-2fa` - 禁用2FA

**house/** (房源)
- `/house/` - 首页
- `/house/<id>` - 详情
- `/house/create` - 发布
- `/house/<id>/edit` - 编辑
- `/house/<id>/delete` - 删除
- `/house/my-houses` - 我的房源
- `/house/api/search` - API搜索

**user/** (用户)
- `/user/profile` - 个人资料
- `/user/leases` - 我的合同
- `/user/messages` - 收件箱
- `/user/sent-messages` - 已发送
- `/user/viewings` - 我的预约

**search/** (搜索)
- `/search/` - 搜索页面
- `/search/recommendations` - 智能推荐

**message/** (消息)
- `/message/send` - 发送消息
- `/message/reply/<id>` - 回复
- `/message/delete/<id>` - 删除
- `/message/news` - 新闻列表
- `/message/news/<id>` - 新闻详情
- `/message/news/create` - 创建新闻
- `/message/api/unread-count` - 未读数API

**lease/** (租赁)
- `/lease/viewing/<house_id>` - 预约看房
- `/lease/viewings/manage` - 管理预约
- `/lease/contract/create/<house_id>` - 创建合同
- `/lease/contract/<id>` - 合同详情
- `/lease/contract/<id>/sign` - 签署合同
- `/lease/contract/<id>/download` - 下载合同
- `/lease/payment/<contract_id>` - 支付租金

**repair/** (维修)
- `/repair/repair/create` - 提交维修
- `/repair/repair/my-repairs` - 我的维修
- `/repair/repair/<id>` - 维修详情
- `/repair/complaint/create` - 提交投诉
- `/repair/complaint/my-complaints` - 我的投诉
- `/repair/complaint/<id>` - 投诉详情

**stats/** (统计) - 仅管理员
- `/stats/` - 仪表板
- `/stats/users` - 用户统计
- `/stats/houses` - 房源统计
- `/stats/financial` - 财务统计
- `/stats/activity` - 活跃度统计

**monitor/** (监控) - 仅管理员
- `/monitor/` - 监控仪表板
- `/monitor/logs` - 日志查看
- `/monitor/logs/clear` - 清空日志
- `/monitor/users/manage` - 用户管理
- `/monitor/health` - 健康检查
- `/monitor/api/stats` - 系统统计API

## 数据流转示例

### 用户注册流程
```
用户访问 /auth/register
    ↓
GET请求 → 显示注册表单 (RegistrationForm)
    ↓
用户填写并提交
    ↓
POST请求 → 表单验证
    ↓
验证通过 → 创建User对象
    ↓
密码加密 (bcrypt)
    ↓
保存到数据库
    ↓
发送验证邮件 (异步)
    ↓
记录系统日志
    ↓
重定向到登录页面
```

### 房源发布流程
```
房东访问 /house/create
    ↓
GET请求 → 显示房源表单 (HouseForm)
    ↓
用户填写信息并上传图片
    ↓
POST请求 → 表单验证
    ↓
验证通过 → 创建House对象
    ↓
保存图片到 static/uploads/houses/
    ↓
图片路径转为JSON存入数据库
    ↓
保存到数据库
    ↓
重定向到房源详情页
```

### 合同签署流程
```
租客访问 /lease/contract/create/<house_id>
    ↓
填写合同信息 (租期、租金等)
    ↓
POST请求 → 创建LeaseContract
    ↓
状态: pending (待签署)
    ↓
房东访问合同详情
    ↓
点击签署 → signed_by_landlord = True
    ↓
租客点击签署 → signed_by_tenant = True
    ↓
双方都签署 → status = 'active'
    ↓
自动生成PDF合同 (reportlab)
    ↓
保存到 static/uploads/contracts/
    ↓
可下载PDF
```

## 技术架构特点

### 1. 分层架构
```
表现层 (Templates + Bootstrap)
    ↓
控制层 (Blueprint Views)
    ↓
业务层 (Forms + Utils)
    ↓
数据层 (Models + SQLAlchemy)
```

### 2. 模块化设计
- 8个独立蓝图模块
- 职责清晰，易于维护
- 可单独测试

### 3. 安全性
- 多层防护（CSRF、XSS、SQL注入）
- 密码加密存储
- 双因素认证
- 权限控制（基于角色）

### 4. 可扩展性
- 应用工厂模式
- 配置驱动
- 插件化扩展
- RESTful API

---

**总代码量**: 约3500+行Python代码
**模板文件**: 10+个HTML模板
**数据库表**: 10个
**路由端点**: 60+个
