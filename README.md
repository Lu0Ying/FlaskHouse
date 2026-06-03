# 智能房屋租赁系统

基于 Flask 框架开发的智能房屋租赁平台，提供房源管理、在线签约、智能搜索、房源图片展示等功能。

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

### 方式一：一键启动（推荐，Windows）

直接双击运行 `rental_system/start.bat`，自动完成所有配置。

### 方式二：手动安装

```bash
# 1. 进入项目目录
cd rental_system

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
venv\Scripts\activate.bat  # Windows
source venv/bin/activate   # Linux/Mac

# 4. 安装依赖
pip install -r requirements.txt

# 5. 初始化数据库（两种方式选其一）
# 方式 A：使用脚本自动初始化（创建表结构 + 导入完整示例数据）
python setup_database.py --import-data
# 方式 B：手动执行 SQL
mysql -u root -p < init_mysql.sql
# 方式 B2：手动执行 SQL（创建表结构 + 导入完整示例数据）
mysql -u root -p rental_system < rental_system.sql

# 6. 启动应用
python run.py
```

访问 <http://localhost:5000>

## 默认账户

### 管理员账户

- **邮箱**: admin@rentalsystem.com
- **密码**: admin123

### 示例用户账户（导入示例数据后可用）

- **房东1**: landlord@example.com / landlord123
- **房东2**: landlord1@example.com / landlord123
- **租客1**: tenant@example.com / tenant123
- **租客2**: tenant1@example.com / tenant123

## 房源图片系统

### 图片存储位置

房源图片存储在 `app/static/uploads/` 目录下。

### 图片命名规则

图片采用 `{房源ID}_{序号}.png` 格式命名：

| 格式 | 说明 | 示例 |
|------|------|------|
| `{house_id}_0.png` | 房源列表展示图（缩略图） | `1_0.png` |
| `{house_id}_1.png` | 详情页第一张轮播图 | `1_1.png` |
| `{house_id}_2.png` | 详情页第二张轮播图 | `1_2.png` |
| ... | ... | ... |

### 图片数据库关联

每张图片在 `house_media` 表中有一条记录：

```sql
INSERT INTO house_media (house_id, media_type, url, `order`, created_at)
VALUES (1, 'image', 'uploads/1_0.png', 0, '2026-05-31 16:23:54');
```

- `house_id`: 关联的房源ID
- `media_type`: 文件类型（image/video）
- `url`: 文件路径（相对于 static 目录）
- `order`: 排序序号（0 为列表展示图，其他为详情页轮播图）

### 添加新房源图片

1. 将图片放入 `app/static/uploads/` 目录
2. 按照命名规则重命名图片（如 `1_0.png`）
3. 在 `house_media` 表中添加对应的数据库记录

## 数据库配置

### MySQL（推荐）

编辑 `rental_system/.env` 文件：

```env
DATABASE_URL=mysql+pymysql://root:123456@localhost/rental_system
```

或者修改 `config.py`：

```python
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@localhost/rental_system'
```

### SQLite（开发测试）

```env
DATABASE_URL=sqlite:///rental_system.db
```

## 配置文件说明

| 文件 | 功能 |
| --- | --- |
| `config.py` | 应用核心配置（数据库连接、邮件服务、文件上传等） |
| `setup_database.py` | 数据库初始化脚本（创建库、执行SQL、初始化数据） |
| `start.bat` | Windows 一键启动脚本（创建虚拟环境、安装依赖、启动应用） |
| `init_mysql.sql` | MySQL 数据库初始化 SQL 文件（仅表结构 + 基础数据） |
| `rental_system.sql` | MySQL 数据库完整备份文件（表结构 + 完整示例数据） |
| `add_house_images.py` | 房源图片数据库导入脚本 |
| `rename_house_images.py` | 房源图片重命名脚本 |
| `app/data/__init__.py` | 地区数据初始化函数 |
| `app/data/regions_data.py` | 行政区划数据（省/市/区） |

## 项目结构

```
FlaskHouse/
├── README.md                    # 项目说明
└── rental_system/              # 主应用目录
    ├── app/                     # Flask应用
    │   ├── __init__.py          # 应用工厂
    │   ├── models.py            # 数据模型
    │   ├── data/                # 初始化数据
    │   │   ├── __init__.py      # 初始化函数
    │   │   ├── __main__.py      # 命令行入口
    │   │   └── regions_data.py  # 行政区划数据
    │   ├── house/               # 房源模块
    │   ├── search/              # 搜索模块
    │   ├── templates/           # HTML模板
    │   └── static/              # 静态资源
    │       └── uploads/         # 上传文件目录
    │           └── *.png        # 房源图片
    ├── tests/                   # 单元测试
    ├── .env                     # 环境变量
    ├── run.py                   # 启动入口
    ├── config.py                # 配置文件
    ├── setup_database.py        # 数据库初始化脚本
    ├── start.bat                # 一键启动脚本
    ├── init_mysql.sql           # MySQL初始化SQL
    ├── rental_system.sql        # MySQL完整备份SQL
    └── requirements.txt         # Python依赖
```

## 主要功能

- ✅ 用户认证（注册、登录、双因素认证）
- ✅ 房源管理（发布、编辑、搜索、图片展示）
- ✅ 房源图片（列表缩略图、详情页轮播图）
- ✅ 省/市/区三级联动选择
- ✅ 租赁管理（预约、合同、支付）
- ✅ 消息系统（站内消息、新闻公告）
- ✅ 维修投诉（维修申请、投诉处理）
- ✅ 报表统计（数据可视化）
- ✅ 系统监控（日志、用户管理）

## 文档说明

| 文件 | 说明 |
| --- | --- |
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
