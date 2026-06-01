from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.news import bp
from app.models import News


@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')

    query = News.query.filter_by(status='published')

    if category:
        query = query.filter_by(category=category)

    news_list = query.order_by(News.published_at.desc()).paginate(page=page, per_page=10)
    return render_template('news/index.html', news_list=news_list, category=category)


@bp.route('/<int:id>')
def detail(id):
    news = News.query.get_or_404(id)
    if news.status != 'published' and (not current_user.is_authenticated or
            (current_user.id != news.publisher_id and not current_user.is_admin())):
        flash('文章不存在或已下架', 'warning')
        return redirect(url_for('news.index'))
    return render_template('news/detail.html', news=news)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.is_landlord() and not current_user.is_admin():
        flash('只有房东或管理员可以发布新闻', 'danger')
        return redirect(url_for('house.index'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        category = request.form.get('category', '')
        action = request.form.get('action', 'draft')

        if not title or not content:
            flash('请填写标题和内容', 'danger')
            return redirect(url_for('news.create'))

        news = News(
            publisher_id=current_user.id,
            title=title,
            content=content,
            category=category,
            status='published' if action == 'publish' else 'draft',
            published_at=datetime.now() if action == 'publish' else None
        )
        db.session.add(news)
        db.session.commit()

        flash('新闻发布成功' if action == 'publish' else '草稿已保存', 'success')
        return redirect(url_for('news.my_news'))

    return render_template('news/create.html')


@bp.route('/my-news')
@login_required
def my_news():
    if not current_user.is_landlord() and not current_user.is_admin():
        flash('无权访问', 'danger')
        return redirect(url_for('house.index'))

    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')

    query = News.query.filter_by(publisher_id=current_user.id)

    if status:
        query = query.filter_by(status=status)

    news_list = query.order_by(News.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('news/my_news.html', news_list=news_list, status=status)


@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    news = News.query.get_or_404(id)

    if current_user.id != news.publisher_id and not current_user.is_admin():
        flash('无权编辑此文章', 'danger')
        return redirect(url_for('news.my_news'))

    if request.method == 'POST':
        news.title = request.form.get('title', '').strip()
        news.content = request.form.get('content', '').strip()
        news.category = request.form.get('category', '')
        action = request.form.get('action', 'draft')

        if action == 'publish' and news.status != 'published':
            news.status = 'published'
            news.published_at = datetime.now()

        db.session.commit()
        flash('修改已保存', 'success')
        return redirect(url_for('news.my_news'))

    return render_template('news/edit.html', news=news)


@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    news = News.query.get_or_404(id)

    if current_user.id != news.publisher_id and not current_user.is_admin():
        flash('无权删除此文章', 'danger')
        return redirect(url_for('news.my_news'))

    db.session.delete(news)
    db.session.commit()
    flash('已删除', 'success')
    return redirect(url_for('news.my_news'))


@bp.route('/publish/<int:id>', methods=['POST'])
@login_required
def publish(id):
    news = News.query.get_or_404(id)

    if current_user.id != news.publisher_id and not current_user.is_admin():
        flash('无权发布此文章', 'danger')
        return redirect(url_for('news.my_news'))

    news.status = 'published'
    news.published_at = datetime.now()
    db.session.commit()
    flash('文章已发布', 'success')
    return redirect(url_for('news.my_news'))


@bp.route('/archive/<int:id>', methods=['POST'])
@login_required
def archive(id):
    news = News.query.get_or_404(id)

    if current_user.id != news.publisher_id and not current_user.is_admin():
        flash('无权归档此文章', 'danger')
        return redirect(url_for('news.my_news'))

    news.status = 'archived'
    db.session.commit()
    flash('文章已归档', 'success')
    return redirect(url_for('news.my_news'))
