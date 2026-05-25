@echo off
echo ========================================
echo   智能房屋租赁系统 - 快速启动脚本
echo ========================================
echo.

REM 检查虚拟环境
if not exist "venv" (
    echo [1/4] 创建虚拟环境...
    python -m venv venv
) else (
    echo [1/4] 虚拟环境已存在
)

REM 激活虚拟环境
echo [2/4] 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo [3/4] 安装依赖包...
pip install -r requirements.txt

REM 初始化数据库
echo [4/4] 初始化数据库...
set FLASK_APP=run.py
flask db init 2>nul
if errorlevel 1 (
    echo 数据库迁移目录已存在，跳过初始化
)
flask db migrate -m "auto migration"
flask db upgrade

echo.
echo ========================================
echo   安装完成！
echo ========================================
echo.
echo 默认管理员账户:
echo   邮箱: admin@rentalsystem.com
echo   密码: admin123
echo.
echo 正在启动服务器...
echo 访问地址: http://localhost:5000
echo.
python run.py
