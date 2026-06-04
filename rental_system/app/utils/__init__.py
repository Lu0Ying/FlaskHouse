import json
from datetime import datetime, timezone, timedelta
from flask import request


def get_client_ip():
    """获取客户端IP地址"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr


def log_action(action, user_id=None, details=None, ip=None):
    """
    记录系统日志
    :param action: 操作描述
    :param user_id: 用户ID（可选）
    :param details: 详细信息（可选，可以是字典或字符串）
    :param ip: IP地址（可选，默认自动获取）
    """
    from app import db
    from app.models import SystemLog
    
    # 自动获取IP
    if ip is None:
        ip = get_client_ip()
    
    # 处理details参数
    if details is None:
        details_str = None
    elif isinstance(details, dict):
        details_str = json.dumps(details, ensure_ascii=False)
    else:
        details_str = str(details)
    
    log = SystemLog(
        action=action,
        user_id=user_id,
        ip=ip,
        details=details_str,
        created_at=datetime.now(timezone(timedelta(hours=8)))
    )
    db.session.add(log)
    db.session.commit()


def record_activity(user_id, action_type, details=None):
    """
    记录用户活动
    :param user_id: 用户ID
    :param action_type: 活动类型
    :param details: 详细信息（可选，可以是字典或字符串）
    """
    from app import db
    from app.models import UserActivity
    
    if details is None:
        details_str = None
    elif isinstance(details, dict):
        details_str = json.dumps(details, ensure_ascii=False)
    else:
        details_str = str(details)
    
    activity = UserActivity(
        user_id=user_id,
        action_type=action_type,
        details=details_str,
        timestamp=datetime.now(timezone(timedelta(hours=8)))
    )
    db.session.add(activity)
    db.session.commit()