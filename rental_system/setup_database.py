#!/usr/bin/env python3
"""
智能房屋租赁系统 - MySQL 数据库初始化脚本

使用方法:
    python setup_database.py
    或
    python setup_database.py --host localhost --user root --password your_password

确保已安装依赖:
    pip install pymysql
"""

import argparse
import pymysql
import os
import sys

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='初始化 MySQL 数据库')
    parser.add_argument('--host', default='localhost', help='MySQL 主机地址')
    parser.add_argument('--port', type=int, default=3306, help='MySQL 端口')
    parser.add_argument('--user', default='root', help='MySQL 用户名')
    parser.add_argument('--password', default='123456', help='MySQL 密码')
    parser.add_argument('--database', default='rental_system', help='数据库名称')
    return parser.parse_args()

def print_info(message):
    """安全打印信息（处理编码问题）"""
    try:
        print(message)
    except UnicodeEncodeError:
        print(message.encode('utf-8').decode('gbk', errors='replace'))

def execute_sql_statements(connection, sql_statements):
    """执行 SQL 语句列表"""
    cursor = connection.cursor()
    success_count = 0
    fail_count = 0
    
    for i, statement in enumerate(sql_statements):
        statement = statement.strip()
        if not statement or statement.startswith('--'):
            continue
        
        try:
            cursor.execute(statement)
            connection.commit()
            success_count += 1
            print_info(f'[OK] 执行语句 {i+1}/{len(sql_statements)}')
        except Exception as e:
            fail_count += 1
            print_info(f'[FAIL] 执行语句 {i+1} 失败: {e}')
            print_info(f'   SQL: {statement[:100]}...')
            connection.rollback()
    
    cursor.close()
    return success_count, fail_count

def main():
    args = parse_args()
    
    print_info('=' * 60)
    print_info('智能房屋租赁系统 - MySQL 数据库初始化')
    print_info('=' * 60)
    print_info(f'连接信息:')
    print_info(f'  主机: {args.host}:{args.port}')
    print_info(f'  用户: {args.user}')
    print_info(f'  数据库: {args.database}')
    print_info('=' * 60)
    
    try:
        connection = pymysql.connect(
            host=args.host,
            port=args.port,
            user=args.user,
            password=args.password,
            charset='utf8mb4'
        )
        
        print_info('[OK] 成功连接到 MySQL 服务器')
        
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {args.database} DEFAULT CHARACTER SET utf8mb4")
        cursor.execute(f"USE {args.database}")
        connection.commit()
        cursor.close()
        
        print_info(f'[OK] 成功创建/选择数据库: {args.database}')
        
        sql_file_path = os.path.join(os.path.dirname(__file__), 'init_mysql.sql')
        
        if not os.path.exists(sql_file_path):
            print_info(f'[FAIL] SQL 文件不存在: {sql_file_path}')
            return
        
        print_info(f'\n开始执行 SQL 文件: {sql_file_path}')
        print_info('-' * 60)
        
        # 读取并分割 SQL 文件
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 按分号分割，但要处理字符串中的分号
        statements = []
        current = ''
        in_string = False
        string_char = ''
        comment_block = False
        
        for char in content:
            # 处理多行注释
            if char == '/' and not in_string:
                # 检查下一个字符
                peek = content[content.index(char) + 1] if content.index(char) + 1 < len(content) else ''
                if peek == '*':
                    comment_block = True
                    current += char
                    continue
            
            if comment_block:
                current += char
                if char == '*' and content[content.index(char) + 1] == '/':
                    comment_block = False
                continue
            
            # 处理字符串边界
            if (char == "'" or char == '"') and not comment_block:
                if not in_string:
                    in_string = True
                    string_char = char
                elif string_char == char:
                    # 检查是否是转义字符
                    if current[-1] != '\\':
                        in_string = False
            
            # 遇到分号且不在字符串中时，结束当前语句
            if char == ';' and not in_string and not comment_block:
                statements.append(current.strip())
                current = ''
            else:
                current += char
        
        # 添加最后一个语句（如果有）
        if current.strip():
            statements.append(current.strip())
        
        print_info(f'共解析到 {len(statements)} 条 SQL 语句')
        
        # 执行所有语句
        success_count, fail_count = execute_sql_statements(connection, statements)
        
        print_info('-' * 60)
        print_info(f'执行完成! 成功: {success_count}, 失败: {fail_count}')
        
        if fail_count == 0:
            print_info('')
            print_info('数据库初始化完成！')
            print_info('')
            print_info('默认管理员账户:')
            print_info('  邮箱: admin@rentalsystem.com')
            print_info('  密码: admin123')
            print_info('')
            print_info('下一步:')
            print_info('  1. 确保 .env 文件中的数据库配置正确')
            print_info('  2. 运行 python run.py 启动应用')
        
        connection.close()
        
    except pymysql.err.OperationalError as e:
        print_info(f'[FAIL] 数据库连接失败: {e}')
        print_info('请检查:')
        print_info('  1. MySQL 服务是否启动')
        print_info('  2. 用户名和密码是否正确')
        print_info('  3. 网络连接是否正常')
    except Exception as e:
        print_info(f'[FAIL] 发生未知错误: {e}')
        import traceback
        print_info(traceback.format_exc())

if __name__ == '__main__':
    main()