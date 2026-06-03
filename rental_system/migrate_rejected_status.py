"""
迁移脚本：为租赁合同添加'rejected'状态
此脚本将更新数据库以支持新的合同状态
"""
from app import create_app, db
from app.models import LeaseContract

def migrate():
    app = create_app()
    with app.app_context():
        print("开始迁移：添加'rejected'状态支持...")
        
        # 查找所有现有合同（不需要修改，因为status字段是字符串类型）
        contracts = LeaseContract.query.all()
        print(f"找到 {len(contracts)} 个合同记录")
        
        # 统计各状态的合同数量
        status_counts = {}
        for contract in contracts:
            status_counts[contract.status] = status_counts.get(contract.status, 0) + 1
        
        print("\n当前合同状态分布：")
        for status, count in status_counts.items():
            print(f"  - {status}: {count}")
        
        print("\n迁移完成！")
        print("'rejected'状态已可用，房东拒绝合同后将保留记录并标记为'rejected'")

if __name__ == '__main__':
    migrate()
