# contract.py module
from datetime import datetime, date
import calendar


def calculate_next_date(current_date, months=1):
    """
    计算指定日期加上指定月数后的日期
    """
    year = current_date.year + (current_date.month + months - 1) // 12
    month = (current_date.month + months - 1) % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    day = min(current_date.day, last_day)
    return date(year, month, day)


def calculate_months_between(start, end):
    """
    计算两个日期之间的月数（包括部分月份）
    """
    if start >= end:
        return 0
    
    years = end.year - start.year
    months = end.month - start.month
    total_months = years * 12 + months
    
    # 如果结束日期的天数小于开始日期的天数，则减去一个月
    if end.day < start.day:
        total_months -= 1
    
    return total_months


def generate_rent_payments(contract):
    """
    为租赁合同生成租金支付记录
    :param contract: LeaseContract 实例
    :return: RentPayment 实例列表
    """
    payments = []
    current_start = contract.start_date
    
    # 根据支付方式确定月数
    if contract.payment_method == 'monthly':
        cycle_months = 1
    elif contract.payment_method == 'quarterly':
        cycle_months = 3
    elif contract.payment_method == 'yearly':
        cycle_months = 12
    else:
        cycle_months = 1  # 默认按月
    
    while current_start < contract.end_date:
        # 计算当前周期的理论结束日期
        theoretical_end = calculate_next_date(current_start, cycle_months)
        
        # 实际结束日期不超过合同结束日期
        actual_end = min(theoretical_end, contract.end_date)
        
        # 计算当前周期包含的月数
        months_in_cycle = calculate_months_between(current_start, actual_end)
        
        # 如果不足一个完整月，仍按一个月计算
        if months_in_cycle <= 0:
            months_in_cycle = 1
        
        # 计算本期租金金额
        cycle_amount = contract.rent_amount * months_in_cycle
        
        # 创建支付记录
        payment = {
            'contract_id': contract.id,
            'amount': cycle_amount,
            'start_date': current_start,
            'end_date': actual_end,
            'due_date': actual_end,  # 付款到期日设为周期结束日
            'status': 'unpaid'
        }
        payments.append(payment)
        
        # 移动到下一周期
        current_start = theoretical_end
    
    return payments
