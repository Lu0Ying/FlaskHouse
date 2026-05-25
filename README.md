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

## 快速开始

```bash
# 1. 进入项目目录
cd rental_system

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行应用
python run.py
```

访问 http://localhost:5000

## 默认管理员账户

- **邮箱**: admin@rentalsystem.com
- **密码**: admin123

## 数据库配置

### MySQL（推荐）
编辑 `rental_system/.env` 文件：
```env
DATABASE_URL=mysql+pymysql://root:123456@localhost/rental_system
```

### SQLite（开发测试）
```env
DATABASE_URL=sqlite:///rental_system.db
```

## 项目结构

```
FlaskHouse/
├── README.md                    # 项目说明
└── rental_system/               # 主应用目录
    ├── app/                     # Flask应用
    ├── tests/                   # 单元测试
    ├── .env                     # 环境变量
    ├── run.py                   # 启动入口
    ├── config.py                # 配置文件
    ├── requirements.txt         # Python依赖
    └── docs/ (各类md文档)
```

## 主要功能

- ✅ 用户认证（注册、登录、双因素认证）
- ✅ 房源管理（发布、编辑、搜索）
- ✅ 租赁管理（预约、合同、支付）
- ✅ 消息系统（站内消息、新闻公告）
- ✅ 维修投诉（维修申请、投诉处理）
- ✅ 报表统计（数据可视化）
- ✅ 系统监控（日志、用户管理）

## 文档说明

| 文件 | 说明 |
|------|------|
| `rental_system/README.md` | 应用详细说明 |
| `rental_system/QUICKSTART.md` | 快速参考指南 |
| `rental_system/PROJECT_SUMMARY.md` | 项目功能总结 |
| `rental_system/STRUCTURE.md` | 项目结构说明 |
| `rental_system/DEPLOYMENT.md` | 部署指南 |
| `rental_system/CHECKLIST.md` | 功能检查清单 |

## 运行测试

```bash
cd rental_system
pytest tests/ -v
```

## 许可证

MIT License