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
        receiver_id = request.form.get('receiver_id', type=int)
        content = request.form.get('content', '').strip()
        house_id = request.form.get('house_id', type=int)

        if not receiver_id or not content:
            flash('请选择收件人并填写消息内容', 'danger')
            return redirect(url_for('message.send'))

        receiver = User.query.get(receiver_id)
        if not receiver:
            flash('收件人不存在', 'danger')
            return redirect(url_for('message.send'))

        message = Message(
            sender_id=current_user.id,
            receiver_id=receiver_id,
            content=content,
            type='message'
        )
        db.session.add(message)

        if house_id:
            reply_content = get_auto_reply(content)
            auto_message = Message(
                sender_id=receiver_id,
                receiver_id=current_user.id,
                content=f'【智能回复】{reply_content}',
                type='notification'
            )
            db.session.add(auto_message)

        db.session.commit()
        flash('消息发送成功', 'success')
        return redirect(url_for('message.sent'))

    users = User.query.filter(User.id != current_user.id).all()
    houses = House.query.filter_by(landlord_id=current_user.id).all() if current_user.is_landlord() else []
    return render_template('message/send.html', users=users, houses=houses)


@bp.route('/reply/<int:user_id>', methods=['GET'])
@login_required
def reply(user_id):
    user = User.query.get_or_404(user_id)
    users = [user]
    return render_template('message/send.html', users=users, reply_to=user)


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

    conversation = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == message.sender_id)) |
        ((Message.sender_id == message.sender_id) & (Message.receiver_id == current_user.id))
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
