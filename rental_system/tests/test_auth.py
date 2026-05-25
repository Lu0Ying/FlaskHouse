import pytest
from app import create_app, db
from app.models import User
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app(TestConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """创建测试运行器"""
    return app.test_cli_runner()


def test_home_page(client):
    """测试首页"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'\xe6\xac\xa2\xe8\xbf\x8e' in response.data  # "欢迎"的UTF-8编码


def test_login_page(client):
    """测试登录页面"""
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b'\xe7\x99\xbb\xe5\xbd\x95' in response.data  # "登录"的UTF-8编码


def test_register_page(client):
    """测试注册页面"""
    response = client.get('/auth/register')
    assert response.status_code == 200
    assert b'\xe6\xb3\xa8\xe5\x86\x8c' in response.data  # "注册"的UTF-8编码


def test_user_registration(client):
    """测试用户注册"""
    response = client.post('/auth/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass123',
        'password2': 'testpass123',
        'role': 'tenant'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # 验证用户已创建
    user = User.query.filter_by(email='test@example.com').first()
    assert user is not None
    assert user.username == 'testuser'


def test_user_login(client):
    """测试用户登录"""
    # 先注册用户
    client.post('/auth/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass123',
        'password2': 'testpass123',
        'role': 'tenant'
    })
    
    # 测试登录
    response = client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'testpass123'
    }, follow_redirects=True)
    
    assert response.status_code == 200


def test_protected_route_requires_login(client):
    """测试受保护的路由需要登录"""
    response = client.get('/user/profile')
    assert response.status_code == 302  # 重定向到登录页
    assert '/auth/login' in response.location


def test_house_creation(client):
    """测试房源创建（需要先登录）"""
    # 注册并登录房东用户
    client.post('/auth/register', data={
        'username': 'landlord1',
        'email': 'landlord@example.com',
        'password': 'testpass123',
        'password2': 'testpass123',
        'role': 'landlord'
    })
    
    client.post('/auth/login', data={
        'email': 'landlord@example.com',
        'password': 'testpass123'
    })
    
    # 创建房源
    response = client.post('/house/create', data={
        'title': 'Test House',
        'address': '123 Test St',
        'district': 'Test District',
        'city': 'Test City',
        'price': 1000.0,
        'deposit': 2000.0,
    }, follow_redirects=True)
    
    assert response.status_code == 200


def test_api_search(client):
    """测试API搜索"""
    response = client.get('/house/api/search?keyword=test')
    assert response.status_code == 200
    assert response.content_type == 'application/json'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
