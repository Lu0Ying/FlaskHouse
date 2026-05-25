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
│   │   ├── security.py    # 安全相关（密码加密、2FA）
│   │   ├── email.py       # 邮件发送
│   │   ├── file_upload.py # 文件上传
│   │   └── contract.py    # PDF合同生成
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

### 1. 安装依赖

```bash
cd rental_system
pip install -r requirements.txt
```

### 2. 配置环境变量

编辑 `.env` 文件，修改以下配置：

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///rental_system.db
MAIL_SERVER=smtp.gmail.com
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-email-password
```

### 3. 初始化数据库

```bash
flask db init
flask db migrate -m "initial migration"
flask db upgrade
```

### 4. 运行应用

```bash
python run.py
```

访问 http://localhost:5000

## 默认管理员账户

系统首次运行时会自动创建管理员账户：

- **邮箱**: admin@rentalsystem.com
- **密码**: admin123

**注意**: 请在生产环境中修改默认密码！

## 主要功能

### 1. 用户认证
- 用户注册/登录
- 邮箱验证
- 双因素认证（2FA）
- 密码重置

### 2. 房源管理
- 房源发布/编辑/删除
- 图片/视频上传
- 房源状态管理
- 我的房源列表

### 3. 智能搜索
- 多条件筛选（价格、区域、户型等）
- 关键词搜索
- 智能推荐算法
- 排序功能

### 4. 租赁管理
- 看房预约
- 合同创建与签署
- PDF合同生成
- 租金支付记录

### 5. 消息系统
- 站内消息
- 消息回复
- 未读消息提醒
- 新闻公告

### 6. 维修与投诉
- 维修申请提交
- 投诉处理
- 状态跟踪

### 7. 报表统计（管理员）
- 用户统计
- 房源统计
- 财务统计
- 活跃度分析

### 8. 系统监控（管理员）
- 系统资源监控
- 日志查看
- 用户管理
- 健康检查

## API接口

### 房源搜索API
```
GET /house/api/search?keyword=test&city=北京&min_price=1000&max_price=5000
```

### 未读消息API
```
GET /message/api/unread-count
```

### 系统健康检查
```
GET /monitor/health
```

## 运行测试

```bash
pytest tests/ -v
```

## 安全建议

1. **生产环境配置**
   - 修改 `SECRET_KEY` 为强随机字符串
   - 使用 PostgreSQL 或 MySQL 替代 SQLite
   - 启用 HTTPS
   - 配置正确的邮件服务器

2. **密码策略**
   - 强制要求复杂密码
   - 定期更换密码
   - 启用双因素认证

3. **文件上传**
   - 限制上传文件大小
   - 验证文件类型
   - 使用对象存储（如 AWS S3）

4. **数据库**
   - 定期备份
   - 使用连接池
   - 启用慢查询日志

## 扩展功能建议

1. **支付集成**: 接入支付宝/微信支付
2. **地图服务**: 集成高德/百度地图显示房源位置
3. **即时通讯**: WebSocket实现实时聊天
4. **移动端**: 开发 React Native 或 Flutter App
5. **数据分析**: 集成数据可视化工具
6. **AI推荐**: 使用机器学习优化推荐算法

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。
