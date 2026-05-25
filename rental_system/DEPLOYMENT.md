# 部署指南

## 开发环境运行

### Windows
```bash
start.bat
```

### Linux/Mac
```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化数据库
export FLASK_APP=run.py
flask db upgrade

# 4. 运行
python run.py
```

## 生产环境部署（Ubuntu + Nginx + Gunicorn）

### 1. 安装系统依赖
```bash
sudo apt update
sudo apt install python3-pip python3-venv nginx supervisor
```

### 2. 配置应用
```bash
# 创建应用目录
sudo mkdir -p /var/www/rental_system
cd /var/www/rental_system

# 复制项目文件
# ... (上传代码)

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install gunicorn psycopg2-binary  # PostgreSQL支持
```

### 3. 配置环境变量
```bash
nano .env
```

修改以下配置：
```env
FLASK_ENV=production
SECRET_KEY=<生成强随机字符串>
DATABASE_URL=postgresql://user:password@localhost/rental_db
MAIL_SERVER=smtp.yourdomain.com
MAIL_USERNAME=noreply@yourdomain.com
MAIL_PASSWORD=<邮件密码>
```

### 4. 配置数据库（PostgreSQL）
```bash
sudo -u postgres psql
CREATE DATABASE rental_db;
CREATE USER rental_user WITH PASSWORD 'strong_password';
GRANT ALL PRIVILEGES ON DATABASE rental_db TO rental_user;
\q

# 初始化数据库
flask db upgrade
```

### 5. 配置Gunicorn
创建 `gunicorn_config.py`:
```python
bind = "127.0.0.1:8000"
workers = 4
timeout = 120
accesslog = "/var/log/rental_system/access.log"
errorlog = "/var/log/rental_system/error.log"
```

### 6. 配置Supervisor
创建 `/etc/supervisor/conf.d/rental_system.conf`:
```ini
[program:rental_system]
command=/var/www/rental_system/venv/bin/gunicorn -c gunicorn_config.py run:app
directory=/var/www/rental_system
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
```

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start rental_system
```

### 7. 配置Nginx
创建 `/etc/nginx/sites-available/rental_system`:
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /var/www/rental_system/app/static;
        expires 30d;
    }

    location /uploads {
        alias /var/www/rental_system/app/static/uploads;
        expires 30d;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/rental_system /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

### 8. 配置SSL（Let's Encrypt）
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

### 9. 配置防火墙
```bash
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## Docker部署（可选）

### 1. 创建 Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN flask db upgrade

CMD ["gunicorn", "-b", "0.0.0.0:8000", "run:app"]
```

### 2. 创建 docker-compose.yml
```yaml
version: '3'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/rental_db
    depends_on:
      - db
  
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: rental_db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### 3. 运行
```bash
docker-compose up -d
```

## 监控与维护

### 查看日志
```bash
# 应用日志
tail -f /var/log/rental_system/error.log

# Nginx日志
tail -f /var/log/nginx/access.log

# Supervisor日志
sudo supervisorctl tail rental_system stderr
```

### 备份数据库
```bash
# PostgreSQL备份
pg_dump rental_db > backup_$(date +%Y%m%d).sql

# 恢复
psql rental_db < backup_20260101.sql
```

### 更新应用
```bash
cd /var/www/rental_system
git pull
source venv/bin/activate
pip install -r requirements.txt
flask db upgrade
sudo supervisorctl restart rental_system
```

## 性能优化建议

1. **启用缓存**
   ```python
   # 安装 Flask-Caching
   pip install Flask-Caching
   
   # 配置Redis缓存
   CACHE_TYPE = 'redis'
   CACHE_REDIS_URL = 'redis://localhost:6379/0'
   ```

2. **数据库优化**
   - 添加适当的索引
   - 使用连接池
   - 定期分析查询性能

3. **静态文件CDN**
   - 使用 Cloudflare 或阿里云CDN
   - 启用Gzip压缩

4. **异步任务**
   - 使用 Celery + Redis 处理邮件发送等耗时任务

## 安全加固

1. ** fail2ban 防护**
   ```bash
   sudo apt install fail2ban
   ```

2. **定期更新**
   ```bash
   pip list --outdated
   pip install --upgrade package_name
   ```

3. **安全头信息**
   ```python
   # 安装 Flask-Talisman
   pip install flask-talisman
   
   from flask_talisman import Talisman
   Talisman(app)
   ```

---

如有问题，请查看日志文件或联系技术支持。
