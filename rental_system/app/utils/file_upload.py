import os
from werkzeug.utils import secure_filename
from flask import current_app
from datetime import datetime


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def save_upload_file(file, subfolder='uploads'):
    """保存上传文件"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{timestamp}{ext}"
        
        upload_folder = os.path.join(current_app.root_path, 'static', subfolder)
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        return f"{subfolder}/{filename}"
    
    return None


def save_multiple_files(files, subfolder='uploads'):
    """保存多个上传文件"""
    saved_files = []
    for file in files:
        if file and file.filename:
            filepath = save_upload_file(file, subfolder)
            if filepath:
                saved_files.append(filepath)
    return saved_files


def delete_file(filepath):
    """删除文件"""
    if filepath:
        full_path = os.path.join(current_app.root_path, 'static', filepath)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
    return False
