"""
快速生成项目文件脚本
运行此脚本将创建所有必需的空白文件
"""
import os

BASE_DIR = r'D:\PyCharmProject\rental_system'

# Python文件
python_files = [
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

# HTML模板文件
template_files = [
    'app/templates/base.html',
    'app/templates/auth/login.html',
    'app/templates/auth/register.html',
    'app/templates/house/index.html',
    'app/templates/house/detail.html',
    'app/templates/house/create.html',
    'app/templates/house/edit.html',
    'app/templates/user/profile.html',
    'app/templates/user/my_houses.html',
    'app/templates/search/search.html',
    'app/templates/message/inbox.html',
    'app/templates/message/send.html',
    'app/templates/lease/contracts.html',
    'app/templates/lease/appointments.html',
    'app/templates/repair/create.html',
    'app/templates/repair/list.html',
    'app/templates/stats/dashboard.html',
    'app/templates/monitor/logs.html',
    'app/templates/monitor/users.html',
    'app/templates/errors/404.html',
    'app/templates/errors/500.html',
]

def create_file(filepath, content=''):
    """创建文件"""
    full_path = os.path.join(BASE_DIR, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    if not os.path.exists(full_path):
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'✓ 创建: {filepath}')
    else:
        print(f'- 已存在: {filepath}')

def main():
    print('=' * 60)
    print('智能房屋租赁系统 - 文件生成工具')
    print('=' * 60)
    print()
    
    # 创建Python文件
    print('📄 创建Python文件...')
    for filepath in python_files:
        if 'forms.py' in filepath:
            content = '# WTForms表单定义\nfrom flask_wtf import FlaskForm\nfrom wtforms import *\nfrom wtforms.validators import *\n'
        elif 'views.py' in filepath:
            module = filepath.split('/')[1]
            content = f'''from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.{module} import bp
from app.models import *

@bp.route('/')
def index():
    return render_template('{module}/index.html')
'''
        else:
            content = f'# {os.path.basename(filepath)} module\n'
        
        create_file(filepath, content)
    
    print()
    print('📝 创建HTML模板...')
    for filepath in template_files:
        if 'base.html' in filepath:
            content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{% block title %}智能房屋租赁系统{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('house.index') }}">房屋租赁系统</a>
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
'''
        elif 'errors/' in filepath:
            error_code = '404' if '404' in filepath else '500'
            content = f'''{{% extends "base.html" %}}
{{% block title %}}{error_code} Error{{% endblock %}}
{{% block content %}}
<h1>{error_code} Error</h1>
<p>页面未找到</p>
<a href="{{{{ url_for('house.index') }}}}" class="btn btn-primary">返回首页</a>
{{% endblock %}}
'''
        else:
            content = '{% extends "base.html" %}\n{% block title %}Page{% endblock %}\n{% block content %}\n<h1>Page Title</h1>\n{% endblock %}\n'
        
        create_file(filepath, content)
    
    print()
    print('=' * 60)
    print('✅ 所有文件创建完成！')
    print('=' * 60)
    print()
    print('下一步:')
    print('1. 完善 app/forms.py - 添加表单类')
    print('2. 完善各个 views.py - 添加路由逻辑')
    print('3. 完善 HTML 模板 - 添加页面内容')
    print('4. 运行: flask db migrate && flask db upgrade')
    print('5. 运行: python run.py')
    print()

if __name__ == '__main__':
    main()
