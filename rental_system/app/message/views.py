from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.message import bp
from app.models import Message, User, House


LANDLORD_AUTO_REPLIES = {
    '租金': '您好，感谢您的咨询！房源租金信息已显示在详情页。如需了解具体付款方式，请告知您偏好的付款周期（月付/季付/年付）。',
    '押金': '房源押金一般为一个月租金，具体可协商。退租时房屋设施完好无损即可全额退还押金。',
    '位置': '房源位于市区核心地段，交通便利，周边配套设施齐全。详情页有具体地址和周边环境介绍。',
    '看房': '欢迎预约看房！请通过系统提交看房预约，我会尽快确认看房时间。',
    '户型': '房源户型信息已在详情页展示，包括房间数量、客厅、厨房、卫生间等。如有疑问欢迎咨询。',
    '面积': '房源建筑面积已在详情页标注。我可以为您提供更详细的房屋布局图。',
    '装修': '房源为精装修，配置齐全，可直接入住。如有特殊需求可协商。',
    '入住': '可协商入住时间，通常提前一周通知即可。欢迎预约看房后再决定。',
    '最短': '最短租期为一年，长租可享受优惠。',
    '宠物': '抱歉，该房源暂不支持宠物入住。',
    '停车': '小区有地下停车场，停车位费用为每月300元。',
    '谢谢': '不客气！如有其他问题随时联系我。祝您早日找到心仪的房源！',
    '你好': '您好！感谢您的咨询。请问有什么可以帮助您的？',
    '请问': '您好，很高兴为您服务。请说具体一点，以便我更好地回答您的问题。',
}

def get_auto_reply(message_content):
    """根据消息内容返回智能自动回复"""
    content = message_content.lower() if message_content else ''
    for keyword, reply in LANDLORD_AUTO_REPLIES.items():
        if keyword in content:
            return reply
    return '感谢您的留言！我会尽快回复您。如有紧急问题，请直接电话联系。'


@bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    tab = request.args.get('tab', 'received')

    if tab == 'sent':
        messages = Message.query.filter_by(sender_id=current_user.id).order_by(
            Message.created_at.desc()).paginate(page=page, per_page=20)
    else:
        messages = Message.query.filter_by(receiver_id=current_user.id).order_by(
            Message.created_at.desc()).paginate(page=page, per_page=20)

    unread_count = Message.query.filter_by(
        receiver_id=current_user.id, read_status=False).count()

    return render_template('message/index.html', messages=messages, tab=tab,
                          unread_count=unread_count)


@bp.route('/inbox')
@login_required
def inbox():
    page = request.args.get('page', 1, type=int)
    messages = Message.query.filter_by(receiver_id=current_user.id).order_by(
        Message.created_at.desc()).paginate(page=page, per_page=20)
    unread_count = Message.query.filter_by(
        receiver_id=current_user.id, read_status=False).count()

    return render_template('message/inbox.html', messages=messages, unread_count=unread_count)


@bp.route('/sent')
@login_required
def sent():
    page = request.args.get('page', 1, type=int)
    messages = Message.query.filter_by(sender_id=current_user.id).order_by(
        Message.created_at.desc()).paginate(page=page, per_page=20)

    return render_template('message/sent.html', messages=messages)


@bp.route('/send', methods=['GET', 'POST'])
@login_required
def send():
    if request.method == 'POST':
        receiver_email = request.form.get('receiver_email', '').strip()
        content = request.form.get('content', '').strip()

        if not receiver_email or not content:
            flash('请填写收件人邮箱并输入消息内容', 'danger')
            return redirect(url_for('message.send'))

        receiver = User.query.filter_by(email=receiver_email).first()
        if not receiver:
            flash('找不到该邮箱对应的用户', 'danger')
            return redirect(url_for('message.send'))

        if receiver.id == current_user.id:
            flash('不能给自己发送消息', 'danger')
            return redirect(url_for('message.send'))

        message = Message(
            sender_id=current_user.id,
            receiver_id=receiver.id,
            content=content,
            type='message'
        )
        db.session.add(message)
        db.session.commit()
        flash('消息发送成功', 'success')
        return redirect(url_for('message.sent'))

    # 从 URL 参数获取预填充邮箱
    receiver_email = request.args.get('receiver_email', '').strip()
    reply_to_user = None
    if receiver_email:
        reply_to_user = User.query.filter_by(email=receiver_email).first()
    
    return render_template('message/send.html', reply_to_email=receiver_email, reply_to_user=reply_to_user)


@bp.route('/reply/<int:user_id>', methods=['GET'])
@login_required
def reply(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('message/send.html', reply_to_email=user.email, reply_to_user=user)


@bp.route('/api/check_email')
@login_required
def check_email():
    """验证邮箱是否存在并返回用户信息"""
    email = request.args.get('email', '').strip()
    
    if not email:
        return jsonify({'exists': False})
    
    user = User.query.filter_by(email=email).first()
    
    if user:
        if user.id == current_user.id:
            return jsonify({'exists': False, 'error': '不能给自己发消息'})
        
        role_display = {
            'landlord': '房东',
            'tenant': '租客',
            'admin': '管理员'
        }
        # 获取用户姓名，优先显示 real_name，如果为空则显示 username，如果都没有则显示占位文案
        display_name = user.real_name or user.username or '对方暂未透露'
        return jsonify({
            'exists': True,
            'user_id': user.id,
            'username': user.username,
            'real_name': user.real_name,
            'display_name': display_name,
            'role': user.role,
            'role_display': role_display.get(user.role, user.role)
        })
    
    return jsonify({'exists': False})


@bp.route('/view/<int:id>')
@login_required
def view(id):
    message = Message.query.get_or_404(id)

    if message.receiver_id != current_user.id and message.sender_id != current_user.id:
        flash('您无权查看此消息', 'danger')
        return redirect(url_for('message.index'))

    if message.receiver_id == current_user.id and not message.read_status:
        message.read_status = True
        db.session.commit()

    # 确定对话的另一方用户
    # 如果是我收到的消息，另一方是发送者；如果是，我发送的消息，另一方是接收者
    if message.receiver_id == current_user.id:
        other_user_id = message.sender_id
    else:
        other_user_id = message.receiver_id

    # 查询我和这个另一方之间的所有消息
    conversation = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == other_user_id)) |
        ((Message.sender_id == other_user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.asc()).all()

    return render_template('message/view.html', message=message, conversation=conversation)


@bp.route('/mark_read/<int:id>', methods=['POST'])
@login_required
def mark_read(id):
    message = Message.query.get_or_404(id)
    if message.receiver_id == current_user.id:
        message.read_status = True
        db.session.commit()
    return jsonify({'status': 'success'})


@bp.route('/mark_all_read', methods=['POST'])
@login_required
def mark_all_read():
    Message.query.filter_by(receiver_id=current_user.id, read_status=False).update(
        {'read_status': True})
    db.session.commit()
    flash('所有消息已标记为已读', 'success')
    return redirect(url_for('message.inbox'))


@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    message = Message.query.get_or_404(id)
    if message.sender_id != current_user.id and message.receiver_id != current_user.id:
        return jsonify({'status': 'error', 'message': '无权删除'}), 403

    db.session.delete(message)
    db.session.commit()
    return jsonify({'status': 'success'})


@bp.route('/unread_count')
@login_required
def unread_count():
    count = Message.query.filter_by(receiver_id=current_user.id, read_status=False).count()
    return jsonify({'count': count})


@bp.route('/api/contacts')
@login_required
def contacts():
    sent_to = db.session.query(Message.receiver_id).filter(
        Message.sender_id == current_user.id).distinct()
    received_from = db.session.query(Message.sender_id).filter(
        Message.receiver_id == current_user.id).distinct()

    contact_ids = set([r[0] for r in sent_to] + [r[0] for r in received_from])
    contacts = User.query.filter(User.id.in_(contact_ids)).all()

    contact_list = []
    for contact in contacts:
        last_msg = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.receiver_id == contact.id)) |
            ((Message.sender_id == contact.id) & (Message.receiver_id == current_user.id))
        ).order_by(Message.created_at.desc()).first()

        unread = Message.query.filter_by(
            sender_id=contact.id, receiver_id=current_user.id, read_status=False).count()

        contact_list.append({
            'id': contact.id,
            'username': contact.username,
            'role': contact.role,
            'last_message': last_msg.content[:50] if last_msg else '',
            'last_time': last_msg.created_at.isoformat() if last_msg else None,
            'unread': unread
        })

    return jsonify({'contacts': contact_list})
