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


# ==================== 分块上传 ====================

def get_chunks_folder():
    """获取分块临时目录"""
    chunks_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'chunks')
    if not os.path.exists(chunks_folder):
        os.makedirs(chunks_folder)
    return chunks_folder


def init_chunk_upload(filename):
    """初始化分块上传，返回 upload_id"""
    import uuid
    upload_id = uuid.uuid4().hex[:16]
    chunk_dir = os.path.join(get_chunks_folder(), upload_id)
    os.makedirs(chunk_dir, exist_ok=True)
    # 保存原始文件名
    meta_path = os.path.join(chunk_dir, '.meta')
    with open(meta_path, 'w', encoding='utf-8') as f:
        f.write(filename)
    return upload_id


def save_chunk(upload_id, chunk_index, chunk_data):
    """保存单个分块"""
    chunk_dir = os.path.join(get_chunks_folder(), upload_id)
    if not os.path.exists(chunk_dir):
        return False
    chunk_path = os.path.join(chunk_dir, f'{chunk_index}.part')
    with open(chunk_path, 'wb') as f:
        f.write(chunk_data)
    return True


def merge_chunks(upload_id, subfolder='uploads'):
    """合并所有分块为最终文件，返回相对路径"""
    chunk_dir = os.path.join(get_chunks_folder(), upload_id)
    if not os.path.exists(chunk_dir):
        return None

    # 读取原始文件名
    meta_path = os.path.join(chunk_dir, '.meta')
    if not os.path.exists(meta_path):
        return None
    with open(meta_path, 'r', encoding='utf-8') as f:
        original_filename = f.read().strip()

    # 获取所有分块并排序
    part_files = [p for p in os.listdir(chunk_dir) if p.endswith('.part')]
    part_files.sort(key=lambda x: int(x.replace('.part', '')))

    # 生成最终文件名
    filename = secure_filename(original_filename)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    name, ext = os.path.splitext(filename)
    filename = f"{name}_{timestamp}{ext}"

    upload_folder = os.path.join(current_app.root_path, 'static', subfolder)
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    final_path = os.path.join(upload_folder, filename)

    # 合并写入
    with open(final_path, 'wb') as outfile:
        for part in part_files:
            part_path = os.path.join(chunk_dir, part)
            with open(part_path, 'rb') as infile:
                outfile.write(infile.read())

    # 清理分块目录
    cleanup_chunks(upload_id)

    return f"{subfolder}/{filename}"


def cleanup_chunks(upload_id):
    """清理分块临时目录"""
    import shutil
    chunk_dir = os.path.join(get_chunks_folder(), upload_id)
    if os.path.exists(chunk_dir):
        shutil.rmtree(chunk_dir, ignore_errors=True)
