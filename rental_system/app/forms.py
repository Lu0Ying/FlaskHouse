# WTForms 表单定义
from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import *


class LoginForm(FlaskForm):
    """登录表单"""
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember = BooleanField('记住我')
    submit = SubmitField('登录')


class RegistrationForm(FlaskForm):
    """注册表单"""
    username = StringField('用户名', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    phone = StringField('手机号', validators=[Length(max=20)])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('角色', choices=[('tenant', '租客'), ('landlord', '房东')], validators=[DataRequired()])
    submit = SubmitField('注册')


class HouseForm(FlaskForm):
    """房源表单"""
    title = StringField('标题', validators=[DataRequired(), Length(max=200)])
    address = StringField('地址', validators=[DataRequired(), Length(max=300)])
    district = StringField('区域', validators=[DataRequired(), Length(max=100)])
    area = StringField('商圈', validators=[Length(max=100)])
    type = SelectField('房屋类型', choices=[('', '请选择'), ('公寓', '公寓'), ('住宅', '住宅'), ('别墅', '别墅')])
    room_count = StringField('户型', validators=[Length(max=20)])
    size = DecimalField('面积 (㎡)', validators=[NumberRange(min=0)])
    rent_price = DecimalField('租金 (元/月)', validators=[DataRequired(), NumberRange(min=0)])
    deposit = DecimalField('押金 (元)', validators=[NumberRange(min=0)])
    decoration = SelectField('装修情况', choices=[('', '请选择'), ('精装', '精装'), ('简装', '简装'), ('毛坯', '毛坯')])
    description = TextAreaField('描述')
    province_code = StringField('省份代码')
    city_code = StringField('城市代码')
    district_code = StringField('区县代码')
    submit = SubmitField('提交')


class MessageForm(FlaskForm):
    """消息表单"""
    receiver_id = IntegerField('接收者 ID')
    content = TextAreaField('内容', validators=[DataRequired()])
    submit = SubmitField('发送')


class RepairForm(FlaskForm):
    """维修申请表单"""
    house_id = IntegerField('房源 ID')
    description = TextAreaField('问题描述', validators=[DataRequired()])
    submit = SubmitField('提交申请')


class ComplaintForm(FlaskForm):
    """投诉表单"""
    house_id = IntegerField('房源 ID')
    content = TextAreaField('投诉内容', validators=[DataRequired()])
    submit = SubmitField('提交投诉')


class NewsForm(FlaskForm):
    """新闻表单"""
    title = StringField('标题', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('内容', validators=[DataRequired()])
    category = SelectField('分类', choices=[('rental', '租赁资讯'), ('repair', '维修指南'), ('notice', '系统公告')], validators=[DataRequired()])
    submit = SubmitField('发布')
