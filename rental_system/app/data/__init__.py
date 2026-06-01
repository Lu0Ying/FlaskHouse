from .regions_data import REGION_DATA

def init_regions_data():
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

    from app import create_app, db
    from app.models import Region

    app = create_app()
    with app.app_context():
        existing_count = Region.query.count()
        print(f'当前数据库中已有 {existing_count} 条地区记录')

        added_count = 0
        for region_data in REGION_DATA:
            existing = Region.query.filter_by(code=region_data['code']).first()
            if not existing:
                region = Region(
                    code=region_data['code'],
                    name=region_data['name'],
                    parent_code=region_data.get('parent_code', ''),
                    level=region_data['level'],
                    is_active=True
                )
                db.session.add(region)
                added_count += 1

        try:
            db.session.commit()
            print(f'成功添加 {added_count} 条新地区记录')
            print(f'地区数据初始化完成！')
            return True
        except Exception as e:
            db.session.rollback()
            print(f'初始化失败: {e}')
            return False


if __name__ == '__main__':
    print('开始初始化行政区划数据...')
    success = init_regions_data()
    import sys
    sys.exit(0 if success else 1)