@echo off
chcp 65001 > nul
echo ========================================
echo   智能房屋租赁系统 - 快速启动脚本
echo ========================================
echo.

REM 检查Python
python --version > nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 检查虚拟环境
if not exist "venv" (
    echo [1/5] 创建虚拟环境...
    python -m venv venv
) else (
    echo [1/5] 虚拟环境已存在
)

REM 激活虚拟环境
echo [2/5] 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo [3/5] 安装依赖包...
pip install -r requirements.txt

REM 初始化数据库
echo [4/5] 初始化数据库...
python setup_database.py --import-data
if errorlevel 1 (
    echo [警告] 数据库初始化可能失败，请检查 MySQL 服务是否启动
)

REM 检查房源图片
echo [5/5] 检查静态资源...
set "UPLOAD_DIR=app\static\uploads"
if not exist "%UPLOAD_DIR%" (
    echo [提示] 上传目录不存在，已自动创建
    mkdir "%UPLOAD_DIR%"
)

echo.
echo ========================================
echo   安装完成！
echo ========================================
echo.
echo 默认管理员账户:
echo   邮箱: admin@rentalsystem.com
echo   密码: admin123
echo.
echo 示例用户账户:
echo   房东: landlord1 / password123
echo   租客: tenant1 / password123
echo.
echo 房源图片说明:
echo   图片位于: app\static\uploads\
echo   命名格式: {房源ID}_{序号}.png
echo   例如: 1_0.png 表示房源1的第一张图片
echo.
echo 正在启动服务器...
echo 访问地址: http://localhost:5000
echo.
python run.py