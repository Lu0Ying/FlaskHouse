# 智能房屋租赁系统

基于 Flask 框架开发的智能房屋租赁平台，提供房源管理、在线签约、智能搜索等功能。

## 技术栈

- **后端框架**: Flask 2.3+
- **数据库**: SQLAlchemy (支持 SQLite/MySQL/PostgreSQL)
- **认证**: Flask-Login
- **表单验证**: Flask-WTF + WTForms
- **数据库迁移**: Flask-Migrate
- **邮件发送**: Flask-Mail
- **密码加密**: bcrypt
- **双因素认证**: pyotp
- **PDF生成**: reportlab
- **测试框架**: pytest

## 项目结构

```
rental_system/
├── .env                    # 环境变量配置
├── requirements.txt        # Python依赖
├── run.py                  # 应用启动入口
├── config.py              # 配置文件
├── app/
│   ├── __init__.py        # 应用工厂
│   ├── models.py          # 数据库模型
│   ├── forms.py           # WTForms表单
│   ├── utils/             # 工具函数
│   ├── auth/              # 认证模块
│   ├── house/             # 房源管理
│   ├── user/              # 用户管理
│   ├── search/            # 智能搜索
│   ├── message/           # 消息与新闻
│   ├── lease/             # 租赁管理
│   ├── repair/            # 维修与投诉
│   ├── stats/             # 报表统计
│   ├── monitor/           # 系统监控
│   ├── templates/         # Jinja2模板
│   └── static/            # 静态资源
└── tests/                 # 单元测试
```

## 安装与运行

### 环境要求
- Python 3.9+
- MySQL 5.7+ / SQLite / PostgreSQL

### 安装步骤

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
# 编辑 .env 文件，配置数据库连接信息

# 3. 运行应用
python run.py
```

### 默认管理员账户
- **邮箱**: admin@rentalsystem.com
- **密码**: admin123

## 数据库配置

### MySQL（推荐）
```env
DATABASE_URL=mysql+pymysql://username:password@localhost/database_name
```

### SQLite（开发测试）
```env
DATABASE_URL=sqlite:///rental_system.db
```

## 功能模块

- ✅ 用户认证（注册、登录、2FA）
- ✅ 房源管理（发布、编辑、搜索）
- ✅ 租赁管理（预约、合同、支付）
- ✅ 消息系统（站内消息、新闻公告）
- ✅ 维修投诉（维修申请、投诉处理）
- ✅ 报表统计（数据可视化）
- ✅ 系统监控（日志、用户管理）

## 开发

```bash
# 启动开发服务器
python run.py

# 数据库迁移
flask db init
flask db migrate -m "描述"
flask db upgrade

# 运行测试
pytest tests/ -v
```

## 文档说明

- **QUICKSTART.md** - 快速参考指南
- **PROJECT_SUMMARY.md** - 项目功能总结
- **STRUCTURE.md** - 项目结构详细说明
- **DEPLOYMENT.md** - 部署指南
- **CHECKLIST.md** - 功能检查清单

## 许可证

MIT License