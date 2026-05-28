#!/usr/bin/env python3
"""
智能房屋租赁系统 - 数据库初始化脚本
使用 Flask-SQLAlchemy 直接创建表结构，确保与模型完全匹配
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, House, News
from werkzeug.security import generate_password_hash

def init_database():
    """初始化数据库"""
    print("=" * 60)
    print("智能房屋租赁系统 - 数据库初始化")
    print("=" * 60)
    
    # 创建应用
    app = create_app()
    
    with app.app_context():
        print("\n[1/4] 正在创建数据库表...")
        
        # 删除所有表（如果存在）
        db.drop_all()
        print("  - 已删除现有表")
        
        # 创建所有表
        db.create_all()
        print("  - 已创建所有表")
        
        print("\n[2/4] 正在插入初始数据...")
        
        # 创建管理员账户
        admin = User(
            username='admin',
            email='admin@rentalsystem.com',
            password_hash=generate_password_hash('admin123'),
            real_name='系统管理员',
            role='admin',
            status='active'
        )
        db.session.add(admin)
        print("  - 已创建管理员账户")
        
        # 创建房东账户
        landlord = User(
            username='landlord1',
            email='landlord@example.com',
            password_hash=generate_password_hash('landlord123'),
            real_name='张房东',
            role='landlord',
            status='active'
        )
        db.session.add(landlord)
        print("  - 已创建房东账户")
        
        # 创建租客账户
        tenant = User(
            username='tenant1',
            email='tenant@example.com',
            password_hash=generate_password_hash('tenant123'),
            real_name='李租客',
            role='tenant',
            status='active'
        )
        db.session.add(tenant)
        print("  - 已创建租客账户")
        
        # 创建示例房源 - 10套精选房源
        house1 = House(
            landlord_id=2,
            title='CBD核心精装两居',
            address='北京市朝阳区建国路88号SOHO现代城',
            district='朝阳区',
            area='CBD',
            type='公寓',
            room_count='2室1厅',
            size=85.5,
            rent_price=5500,
            deposit=11000,
            decoration='精装',
            description='位于CBD核心区域，地铁1号线大望路站步行5分钟，周边配套齐全，拎包入住。',
            status='available'
        )
        db.session.add(house1)
        
        house2 = House(
            landlord_id=2,
            title='中关村学区三居室',
            address='北京市海淀区中关村大街1号科技大厦',
            district='海淀区',
            area='中关村',
            type='住宅',
            room_count='3室2厅',
            size=120,
            rent_price=8000,
            deposit=16000,
            decoration='简装',
            description='学区房，临近中关村一小，地铁4号线中关村站步行3分钟，适合家庭居住。',
            status='available'
        )
        db.session.add(house2)
        
        house3 = House(
            landlord_id=2,
            title='王府井精装一居',
            address='北京市东城区王府井大街10号乐天银泰',
            district='东城区',
            area='王府井',
            type='公寓',
            room_count='1室1厅',
            size=55,
            rent_price=4200,
            deposit=8400,
            decoration='精装',
            description='繁华商业区，购物便利，地铁1号线王府井站直达。',
            status='available'
        )
        db.session.add(house3)
        
        house4 = House(
            landlord_id=2,
            title='金融街舒适两居',
            address='北京市西城区金融街20号国际企业大厦',
            district='西城区',
            area='金融街',
            type='住宅',
            room_count='2室1厅',
            size=78,
            rent_price=6200,
            deposit=12400,
            decoration='精装',
            description='金融中心地段，办公便利，生活配套完善，临近地铁2号线。',
            status='available'
        )
        db.session.add(house4)
        
        house5 = House(
            landlord_id=2,
            title='方庄成熟社区大三居',
            address='北京市丰台区方庄路15号芳城园',
            district='丰台区',
            area='方庄',
            type='住宅',
            room_count='3室2厅',
            size=135,
            rent_price=7500,
            deposit=15000,
            decoration='精装',
            description='成熟社区，配套齐全，临近方庄购物中心，适合大家庭居住。',
            status='available'
        )
        db.session.add(house5)
        
        house6 = House(
            landlord_id=2,
            title='古城Loft公寓',
            address='北京市石景山区古城路8号绿地环球金融城',
            district='石景山区',
            area='古城',
            type='loft',
            room_count='1室1厅',
            size=45,
            rent_price=3800,
            deposit=7600,
            decoration='简装',
            description='Loft户型，挑高4.5米，适合年轻人居住，地铁1号线古城站直达。',
            status='available'
        )
        db.session.add(house6)
        
        house7 = House(
            landlord_id=2,
            title='朝阳公园旁精装公寓',
            address='北京市朝阳区朝阳公园路19号棕榈泉国际公寓',
            district='朝阳区',
            area='朝阳公园',
            type='公寓',
            room_count='2室2厅',
            size=95,
            rent_price=6800,
            deposit=13600,
            decoration='精装',
            description='紧邻朝阳公园，环境优美，空气清新，高端社区配套。',
            status='available'
        )
        db.session.add(house7)
        
        house8 = House(
            landlord_id=2,
            title='五道口精装三居室',
            address='北京市海淀区成府路28号华清嘉园',
            district='海淀区',
            area='五道口',
            type='住宅',
            room_count='3室1厅',
            size=105,
            rent_price=7200,
            deposit=14400,
            decoration='简装',
            description='高校云集，学术氛围浓厚，地铁13号线五道口站步行5分钟。',
            status='available'
        )
        db.session.add(house8)
        
        house9 = House(
            landlord_id=2,
            title='望京SOHO附近公寓',
            address='北京市朝阳区望京街9号望京SOHO',
            district='朝阳区',
            area='望京',
            type='公寓',
            room_count='1室1厅',
            size=48,
            rent_price=4500,
            deposit=9000,
            decoration='精装',
            description='望京商圈核心，办公居住两相宜，地铁14号线望京南站直达。',
            status='available'
        )
        db.session.add(house9)
        
        house10 = House(
            landlord_id=2,
            title='通州核心精装四居',
            address='北京市通州区新华大街50号万达公寓',
            district='通州区',
            area='通州城区',
            type='住宅',
            room_count='4室2厅',
            size=168,
            rent_price=9500,
            deposit=19000,
            decoration='精装',
            description='大型社区，配套完善，临近万达广场，适合多孩家庭。',
            status='available'
        )
        db.session.add(house10)
        print("  - 已创建10套示例房源")
        
        # 创建示例新闻
        news1 = News(
            publisher_id=1,
            title='欢迎使用智能房屋租赁系统',
            content='<p>感谢您使用智能房屋租赁系统！这是一个功能完善的房屋租赁平台，支持房源发布、在线签约、智能搜索等功能。</p><p>祝您使用愉快！</p>',
            category='系统公告',
            status='published'
        )
        db.session.add(news1)
        
        news2 = News(
            publisher_id=1,
            title='平台新功能上线',
            content='<p>我们很高兴地宣布，平台新增了智能推荐功能，可以根据您的浏览历史为您推荐合适的房源。</p>',
            category='功能更新',
            status='published'
        )
        db.session.add(news2)
        print("  - 已创建示例新闻")
        
        # 提交事务
        print("\n[3/4] 正在提交数据...")
        db.session.commit()
        print("  - 数据提交成功")
        
        # 验证数据
        print("\n[4/4] 正在验证数据...")
        user_count = User.query.count()
        house_count = House.query.count()
        news_count = News.query.count()
        
        print(f"  - 用户数量: {user_count}")
        print(f"  - 房源数量: {house_count}")
        print(f"  - 新闻数量: {news_count}")
        
        print("\n" + "=" * 60)
        print("🎉 数据库初始化完成！")
        print("=" * 60)
        print("\n默认账户信息:")
        print("  管理员: admin@rentalsystem.com / admin123")
        print("  房东: landlord@example.com / landlord123")
        print("  租客: tenant@example.com / tenant123")
        print("\n下一步:")
        print("  运行 python run.py 启动应用")

if __name__ == '__main__':
    init_database()
