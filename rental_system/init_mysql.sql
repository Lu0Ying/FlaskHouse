-- ==============================================
-- 智能房屋租赁系统 - MySQL 数据库初始化脚本
-- 与 Flask-SQLAlchemy 模型完全匹配
-- ==============================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS rental_system 
DEFAULT CHARACTER SET utf8mb4 
DEFAULT COLLATE utf8mb4_unicode_ci;

USE rental_system;

-- 临时禁用外键检查，避免 DROP TABLE 顺序问题
SET FOREIGN_KEY_CHECKS = 0;

-- ==============================================
-- 1. 用户表 (users)
-- ==============================================
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    username VARCHAR(64) NOT NULL UNIQUE COMMENT '用户名',
    password_hash VARCHAR(256) NOT NULL COMMENT '密码哈希',
    email VARCHAR(120) NOT NULL UNIQUE COMMENT '邮箱',
    phone VARCHAR(20) COMMENT '手机号',
    role VARCHAR(20) NOT NULL DEFAULT 'tenant' COMMENT '角色: landlord/tenant/admin',
    real_name VARCHAR(100) COMMENT '真实姓名',
    id_card VARCHAR(18) COMMENT '身份证号',
    avatar VARCHAR(256) COMMENT '头像路径',
    status VARCHAR(20) DEFAULT 'active' COMMENT '状态: active/inactive/banned',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    INDEX idx_users_username (username),
    INDEX idx_users_email (email),
    INDEX idx_users_role (role),
    INDEX idx_users_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- ==============================================
-- 2. 房源表 (houses)
-- ==============================================
DROP TABLE IF EXISTS houses;
CREATE TABLE houses (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '房源ID',
    landlord_id INT NOT NULL COMMENT '房东ID',
    title VARCHAR(200) NOT NULL COMMENT '房源标题',
    address VARCHAR(300) NOT NULL COMMENT '详细地址',
    district VARCHAR(100) NOT NULL COMMENT '区域',
    area VARCHAR(100) COMMENT '所属区域/商圈',
    type VARCHAR(50) COMMENT '房屋类型: 公寓/住宅/别墅',
    room_count VARCHAR(20) COMMENT '几室几厅',
    size FLOAT COMMENT '面积(平方米)',
    rent_price FLOAT NOT NULL COMMENT '租金',
    deposit FLOAT DEFAULT 0 COMMENT '押金',
    decoration VARCHAR(50) COMMENT '装修情况: 精装/简装/毛坯',
    description TEXT COMMENT '房源描述',
    status VARCHAR(20) DEFAULT 'available' COMMENT '状态: available/rented/maintenance',
    lat FLOAT COMMENT '纬度',
    lng FLOAT COMMENT '经度',
    province_code VARCHAR(20) COMMENT '省份代码',
    city_code VARCHAR(20) COMMENT '城市代码',
    district_code VARCHAR(20) COMMENT '区县代码',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (landlord_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_houses_landlord_id (landlord_id),
    INDEX idx_houses_district (district),
    INDEX idx_houses_room_count (room_count),
    INDEX idx_houses_rent_price (rent_price),
    INDEX idx_houses_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='房源表';

-- ==============================================
-- 3. 房源媒体文件表 (house_media)
-- ==============================================
DROP TABLE IF EXISTS house_media;
CREATE TABLE house_media (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '媒体ID',
    house_id INT NOT NULL COMMENT '房源ID',
    media_type VARCHAR(20) NOT NULL COMMENT '类型: image/video',
    url VARCHAR(500) NOT NULL COMMENT '文件路径',
    `order` INT DEFAULT 0 COMMENT '排序',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    FOREIGN KEY (house_id) REFERENCES houses(id) ON DELETE CASCADE,
    INDEX idx_house_media_house_id (house_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='房源媒体文件表';

-- ==============================================
-- 4. 租赁合同表 (lease_contracts)
-- ==============================================
DROP TABLE IF EXISTS lease_contracts;
CREATE TABLE lease_contracts (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '合同ID',
    house_id INT NOT NULL COMMENT '房源ID',
    tenant_id INT NOT NULL COMMENT '租客ID',
    landlord_id INT NOT NULL COMMENT '房东ID',
    start_date DATE NOT NULL COMMENT '开始日期',
    end_date DATE NOT NULL COMMENT '结束日期',
    rent_amount FLOAT NOT NULL COMMENT '租金金额',
    deposit_amount FLOAT NOT NULL COMMENT '押金金额',
    payment_method VARCHAR(50) COMMENT '支付方式',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '状态: pending/active/terminated',
    signed_at DATETIME COMMENT '签署时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    FOREIGN KEY (house_id) REFERENCES houses(id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (landlord_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_lease_contracts_house_id (house_id),
    INDEX idx_lease_contracts_tenant_id (tenant_id),
    INDEX idx_lease_contracts_landlord_id (landlord_id),
    INDEX idx_lease_contracts_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='租赁合同表';

-- ==============================================
-- 5. 租金支付记录表 (rent_payments)
-- ==============================================
DROP TABLE IF EXISTS rent_payments;
CREATE TABLE rent_payments (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '支付ID',
    contract_id INT NOT NULL COMMENT '合同ID',
    amount FLOAT NOT NULL COMMENT '支付金额',
    due_date DATE NOT NULL COMMENT '应缴日期',
    paid_date DATE COMMENT '实缴日期',
    status VARCHAR(20) DEFAULT 'unpaid' COMMENT '状态: unpaid/paid/overdue',
    payment_method VARCHAR(50) COMMENT '支付方式',
    transaction_id VARCHAR(100) COMMENT '交易编号',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    FOREIGN KEY (contract_id) REFERENCES lease_contracts(id) ON DELETE CASCADE,
    INDEX idx_rent_payments_contract_id (contract_id),
    INDEX idx_rent_payments_status (status),
    INDEX idx_rent_payments_due_date (due_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='租金支付记录表';

-- ==============================================
-- 6. 看房预约表 (appointments)
-- ==============================================
DROP TABLE IF EXISTS appointments;
CREATE TABLE appointments (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '预约ID',
    house_id INT NOT NULL COMMENT '房源ID',
    tenant_id INT NOT NULL COMMENT '租客ID',
    landlord_id INT NOT NULL COMMENT '房东ID',
    appointment_time DATETIME NOT NULL COMMENT '预约时间',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '状态: pending/confirmed/cancelled/completed',
    remark TEXT COMMENT '备注',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    FOREIGN KEY (house_id) REFERENCES houses(id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (landlord_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_appointments_house_id (house_id),
    INDEX idx_appointments_tenant_id (tenant_id),
    INDEX idx_appointments_status (status),
    INDEX idx_appointments_appointment_time (appointment_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='看房预约表';

-- ==============================================
-- 7. 消息表 (messages)
-- ==============================================
DROP TABLE IF EXISTS messages;
CREATE TABLE messages (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '消息ID',
    sender_id INT NOT NULL COMMENT '发送者ID',
    receiver_id INT NOT NULL COMMENT '接收者ID',
    content TEXT NOT NULL COMMENT '消息内容',
    type VARCHAR(20) DEFAULT 'message' COMMENT '类型: message/notification',
    read_status TINYINT(1) DEFAULT 0 COMMENT '已读状态',
    parent_id INT COMMENT '回复的消息ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES messages(id) ON DELETE CASCADE,
    INDEX idx_messages_sender_id (sender_id),
    INDEX idx_messages_receiver_id (receiver_id),
    INDEX idx_messages_read_status (read_status),
    INDEX idx_messages_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='消息表';

-- ==============================================
-- 8. 新闻公告表 (news)
-- ==============================================
DROP TABLE IF EXISTS news;
CREATE TABLE news (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '新闻ID',
    publisher_id INT NOT NULL COMMENT '发布者ID',
    title VARCHAR(200) NOT NULL COMMENT '标题',
    content TEXT NOT NULL COMMENT '内容',
    category VARCHAR(50) COMMENT '分类',
    status VARCHAR(20) DEFAULT 'draft' COMMENT '状态: draft/published/archived',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    published_at DATETIME COMMENT '发布时间',
    
    FOREIGN KEY (publisher_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_news_publisher_id (publisher_id),
    INDEX idx_news_status (status),
    INDEX idx_news_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='新闻公告表';

-- ==============================================
-- 9. 维修申请表 (repair_requests)
-- ==============================================
DROP TABLE IF EXISTS repair_requests;
CREATE TABLE repair_requests (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '维修ID',
    tenant_id INT NOT NULL COMMENT '租客ID',
    house_id INT NOT NULL COMMENT '房源ID',
    description TEXT NOT NULL COMMENT '问题描述',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '状态: pending/processing/completed/rejected',
    images TEXT COMMENT '图片路径(JSON)',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    resolved_at DATETIME COMMENT '解决时间',
    
    FOREIGN KEY (tenant_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (house_id) REFERENCES houses(id) ON DELETE CASCADE,
    INDEX idx_repair_requests_tenant_id (tenant_id),
    INDEX idx_repair_requests_house_id (house_id),
    INDEX idx_repair_requests_status (status),
    INDEX idx_repair_requests_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='维修申请表';

-- ==============================================
-- 10. 投诉表 (complaints)
-- ==============================================
DROP TABLE IF EXISTS complaints;
CREATE TABLE complaints (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '投诉ID',
    tenant_id INT NOT NULL COMMENT '租客ID',
    house_id INT NOT NULL COMMENT '房源ID',
    title VARCHAR(200) NOT NULL COMMENT '投诉标题',
    content TEXT NOT NULL COMMENT '投诉内容',
    category VARCHAR(50) COMMENT '投诉类别',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '状态: pending/processing/completed/rejected',
    reply TEXT COMMENT '官方回复',
    replied_at DATETIME COMMENT '回复时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    FOREIGN KEY (tenant_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (house_id) REFERENCES houses(id) ON DELETE CASCADE,
    INDEX idx_complaints_tenant_id (tenant_id),
    INDEX idx_complaints_house_id (house_id),
    INDEX idx_complaints_status (status),
    INDEX idx_complaints_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='投诉表';

-- ==============================================
-- 11. 用户活动表 (user_activities)
-- ==============================================
DROP TABLE IF EXISTS user_activities;
CREATE TABLE user_activities (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '活动ID',
    user_id INT NOT NULL COMMENT '用户ID',
    action_type VARCHAR(50) NOT NULL COMMENT '活动类型',
    action_detail TEXT COMMENT '活动详情',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_activities_user_id (user_id),
    INDEX idx_user_activities_action_type (action_type),
    INDEX idx_user_activities_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户活动表';

-- ==============================================
-- 12. 系统日志表 (system_logs)
-- ==============================================
DROP TABLE IF EXISTS system_logs;
CREATE TABLE system_logs (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '日志ID',
    user_id INT COMMENT '操作用户ID',
    action_type VARCHAR(50) NOT NULL COMMENT '操作类型',
    action_detail TEXT COMMENT '操作详情',
    ip_address VARCHAR(50) COMMENT 'IP地址',
    user_agent VARCHAR(500) COMMENT '用户代理',
    log_level VARCHAR(20) DEFAULT 'INFO' COMMENT '日志级别: INFO/WARNING/ERROR/DEBUG',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_system_logs_user_id (user_id),
    INDEX idx_system_logs_action_type (action_type),
    INDEX idx_system_logs_log_level (log_level),
    INDEX idx_system_logs_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统日志表';

-- 恢复外键检查
SET FOREIGN_KEY_CHECKS = 1;

-- ==============================================
-- 插入初始数据
-- ==============================================

-- 插入默认管理员账户
-- 密码为: admin123 (pbkdf2:sha256 Werkzeug加密)
INSERT INTO users (username, email, password_hash, real_name, role, status)
VALUES ('admin', 'admin@rentalsystem.com', 'pbkdf2:sha256:600000$ARS4BLpOEfTGpLmd$cbc65d5a6de44b9132c6ebd9039e97096c128216ea61486b8722a47771774c77', '系统管理员', 'admin', 'active');

-- 插入示例房东账户
-- 密码为: password123 (pbkdf2:sha256 Werkzeug加密)
INSERT INTO users (username, email, password_hash, real_name, role, status)
VALUES ('landlord1', 'landlord@example.com', 'pbkdf2:sha256:600000$ktXC3kuEYXgCtl9S$a2b40d7ca91d548722e4ae86380f78f145751015cd8b3420da5bfe06f59c023d', '张房东', 'landlord', 'active');

-- 插入示例租客账户
-- 密码为: password123 (pbkdf2:sha256 Werkzeug加密)
INSERT INTO users (username, email, password_hash, real_name, role, status)
VALUES ('tenant1', 'tenant@example.com', 'pbkdf2:sha256:600000$ktXC3kuEYXgCtl9S$a2b40d7ca91d548722e4ae86380f78f145751015cd8b3420da5bfe06f59c023d', '李租客', 'tenant', 'active');

-- 插入示例房源（10个房源）
INSERT INTO houses (landlord_id, title, address, district, area, type, room_count, size, rent_price, deposit, decoration, description, status, province_code, city_code, district_code, created_at, updated_at)
VALUES 
(2, 'CBD核心精装两居', '北京市朝阳区建国路88号SOHO现代城', '朝阳区', 'CBD', '公寓', '2室1厅', 85.5, 5500, 11000, '精装', '位于CBD核心区域，地铁1号线大望路站步行5分钟，周边配套齐全，拎包入住。', 'available', NULL, NULL, NULL, '2026-05-31 16:23:54', '2026-05-31 16:23:54'),
(2, '中关村学区三居室', '北京市海淀区中关村大街1号科技大厦', '海淀区', '中关村', '住宅', '3室2厅', 120, 8000, 16000, '简装', '学区房，临近中关村一小，地铁4号线中关村站步行3分钟，适合家庭居住。', 'available', NULL, NULL, NULL, '2026-05-31 16:23:54', '2026-05-31 16:23:54'),
(2, '王府井精装一居', '北京市东城区王府井大街10号乐天银泰', '东城区', '王府井', '公寓', '1室1厅', 55, 4200, 8400, '精装', '繁华商业区，购物便利，地铁1号线王府井站直达。', 'available', NULL, NULL, NULL, '2026-05-31 16:23:54', '2026-05-31 16:23:54'),
(2, '金融街舒适两居', '北京市西城区金融街20号国际企业大厦', '西城区', '金融街', '住宅', '2室1厅', 78, 6200, 12400, '精装', '金融中心地段，办公便利，生活配套完善，临近地铁2号线。', 'available', NULL, NULL, NULL, '2026-05-31 16:23:54', '2026-05-31 16:23:54'),
(2, '方庄成熟社区大三居', '北京市丰台区方庄路15号芳城园', '丰台区', '方庄', '住宅', '3室2厅', 135, 7500, 15000, '精装', '成熟社区，配套齐全，临近方庄购物中心，适合大家庭居住。', 'available', NULL, NULL, NULL, '2026-05-31 16:23:54', '2026-05-31 16:23:54'),
(2, '古城Loft公寓', '北京市石景山区古城路8号绿地环球金融城', '石景山区', '古城', 'loft', '1室1厅', 45, 3800, 7600, '简装', 'Loft户型，挑高4.5米，适合年轻人居住，地铁1号线古城站直达。', 'available', NULL, NULL, NULL, '2026-05-31 16:23:54', '2026-05-31 16:23:54'),
(2, '朝阳公园旁精装公寓', '北京市朝阳区朝阳公园路19号棕榈泉国际公寓', '朝阳区', '朝阳公园', '公寓', '2室2厅', 95, 6800, 13600, '精装', '紧邻朝阳公园，环境优美，空气清新，高端社区配套。', 'available', NULL, NULL, NULL, '2026-05-31 16:23:54', '2026-05-31 16:23:54'),
(2, '五道口精装三居室', '北京市海淀区成府路28号华清嘉园', '海淀区', '五道口', '住宅', '3室1厅', 105, 7200, 14400, '简装', '高校云集，学术氛围浓厚，地铁13号线五道口站步行5分钟。', 'available', NULL, NULL, NULL, '2026-05-31 16:23:54', '2026-05-31 16:23:54'),
(2, '望京SOHO附近公寓', '北京市朝阳区望京街9号望京SOHO', '朝阳区', '望京', '公寓', '1室1厅', 48, 4500, 9000, '精装', '望京商圈核心，办公居住两相宜，地铁14号线望京南站直达。', 'available', NULL, NULL, NULL, '2026-05-31 16:23:54', '2026-05-31 16:23:54'),
(2, '通州核心精装四居', '北京市通州区新华大街50号万达公寓', '通州区', '通州城区', '住宅', '4室2厅', 168, 9500, 19000, '精装', '大型社区，配套完善，临近万达广场，适合多孩家庭。', 'available', NULL, NULL, NULL, '2026-05-31 16:23:54', '2026-05-31 16:23:54');

-- 插入房源图片（house_media）
-- 图片命名格式: {house_id}_{order}.png
-- order=0 的图片为列表展示图，order>0 的图片为详情页轮播图
INSERT INTO house_media (house_id, media_type, url, `order`, created_at)
VALUES 
(1, 'image', 'uploads/1_0.png', 0, '2026-05-31 16:23:54'),
(1, 'image', 'uploads/1_1.png', 1, '2026-05-31 16:23:54'),
(2, 'image', 'uploads/2_0.png', 0, '2026-05-31 16:23:54'),
(2, 'image', 'uploads/2_1.png', 1, '2026-05-31 16:23:54'),
(3, 'image', 'uploads/3_0.png', 0, '2026-05-31 16:23:54'),
(3, 'image', 'uploads/3_1.png', 1, '2026-05-31 16:23:54'),
(3, 'image', 'uploads/3_2.png', 2, '2026-05-31 16:23:54'),
(4, 'image', 'uploads/4_0.png', 0, '2026-05-31 16:23:54'),
(4, 'image', 'uploads/4_1.png', 1, '2026-05-31 16:23:54'),
(5, 'image', 'uploads/5_0.png', 0, '2026-05-31 16:23:54'),
(5, 'image', 'uploads/5_1.png', 1, '2026-05-31 16:23:54'),
(6, 'image', 'uploads/6_0.png', 0, '2026-05-31 16:23:54'),
(6, 'image', 'uploads/6_1.png', 1, '2026-05-31 16:23:54'),
(7, 'image', 'uploads/7_0.png', 0, '2026-05-31 16:23:54'),
(8, 'image', 'uploads/8_0.png', 0, '2026-05-31 16:23:54'),
(9, 'image', 'uploads/9_0.png', 0, '2026-05-31 16:23:54'),
(9, 'image', 'uploads/9_1.png', 1, '2026-05-31 16:23:54'),
(10, 'image', 'uploads/10_0.png', 0, '2026-05-31 16:23:54');

-- 插入示例新闻公告
INSERT INTO news (publisher_id, title, content, category, status, published_at)
VALUES (1, '欢迎使用智能房屋租赁系统', '<p>感谢您使用智能房屋租赁系统！这是一个功能完善的房屋租赁平台，支持房源发布、在线签约、智能搜索等功能。</p><p>祝您使用愉快！</p>', '系统公告', 'published', NOW());

INSERT INTO news (publisher_id, title, content, category, status, published_at)
VALUES (1, '平台新功能上线', '<p>我们很高兴地宣布，平台新增了智能推荐功能，可以根据您的浏览历史为您推荐合适的房源。</p>', '功能更新', 'published', NOW());

-- ==============================================
-- 创建视图
-- ==============================================

-- 活跃合同视图
DROP VIEW IF EXISTS v_active_contracts;
CREATE VIEW v_active_contracts AS
SELECT 
    lc.*,
    h.title AS house_title,
    h.address AS house_address,
    u1.username AS tenant_name,
    u2.username AS landlord_name
FROM lease_contracts lc
JOIN houses h ON lc.house_id = h.id
JOIN users u1 ON lc.tenant_id = u1.id
JOIN users u2 ON lc.landlord_id = u2.id
WHERE lc.status = 'active';

-- 用户统计视图
DROP VIEW IF EXISTS v_user_stats;
CREATE VIEW v_user_stats AS
SELECT 
    role,
    status,
    COUNT(*) AS count
FROM users
GROUP BY role, status;

-- ==============================================
-- 完成提示
-- ==============================================
SELECT '数据库初始化完成！' AS message;
SELECT '默认管理员账户: admin@rentalsystem.com / admin123' AS admin_info;