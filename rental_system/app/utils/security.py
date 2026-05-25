from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(password):
    """密码加密"""
    return generate_password_hash(password)


def verify_password(password_hash, password):
    """验证密码"""
    return check_password_hash(password_hash, password)
