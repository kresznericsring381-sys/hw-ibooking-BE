# 🚀 快速开发指南

> **📝 更新说明 (2026-05-07)**: 已修复数据库字段不匹配问题。`orders`表不包含`room_id`字段，相关查询已通过JOIN `seat`表获取教室信息。

## 📋 目录
1. [快速启动](#快速启动)
2. [数据库初始化](#数据库初始化)
3. [模块开发指南](#模块开发指南)
4. [常用命令](#常用命令)
5. [故障排查](#故障排查)

---

## 快速启动

### 1️⃣ 环境准备

```bash
# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2️⃣ 配置数据库

编辑 `config.py`，修改数据库连接信息：

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '你的密码',  # 改成你的
    'database': 'school',
    'charset': 'utf8mb4',
}
```

### 3️⃣ 初始化数据库

```bash
# 导入数据库备份
mysql -u root -p school < sql/school_backup.sql
```

### 4️⃣ 启动服务

```bash
python app.py
```

访问 http://localhost:5000/api/health 检查服务是否启动

---

## 数据库初始化

### 创建表结构

如果 `school_backup.sql` 中没有包含这些表，手动创建：

```sql
-- 创建教室表
CREATE TABLE room (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    open_time TIME NOT NULL,
    close_time TIME NOT NULL,
    status TINYINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 创建座位表
CREATE TABLE seat (
    id INT PRIMARY KEY AUTO_INCREMENT,
    room_id INT NOT NULL,
    x INT NOT NULL,
    y INT NOT NULL,
    status TINYINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (room_id) REFERENCES room(id),
    UNIQUE KEY (room_id, x, y)
);

-- 创建学生表
CREATE TABLE student (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    password VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 创建订单表
CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id VARCHAR(50) NOT NULL,
    seat_id INT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    status TINYINT DEFAULT 0,
    sign_time DATETIME DEFAULT NULL,
    finish_time DATETIME DEFAULT NULL,
    create_time TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (student_id) REFERENCES student(student_id),
    FOREIGN KEY (seat_id) REFERENCES seat(id),
    INDEX idx_student (student_id),
    INDEX idx_seat (seat_id)
);
```

### 插入测试数据

```sql
-- 插入教室
INSERT INTO room (name, open_time, close_time) VALUES 
('自习室A', '09:00:00', '22:00:00'),
('自习室B', '08:00:00', '23:00:00');

-- 插入学生
INSERT INTO student (student_id, name, password) VALUES 
('2024001', '张三', '123456'),
('2024002', '李四', '123456');
```

---

## 模块开发指南

### 🔧 添加新接口的完整流程

假设需要添加一个"**获取座位详情**"接口：

#### Step 1: 在 DAO 层添加查询方法

**文件**: `dao/seat_dao.py`

```python
@staticmethod
def get_seat_detail(seat_id):
    """根据座位 ID 获取详细信息"""
    sql = """
    SELECT s.*, r.name as room_name,
           COUNT(o.id) as order_count
    FROM seat s
    LEFT JOIN room r ON s.room_id = r.id
    LEFT JOIN orders o ON s.id = o.seat_id AND o.status IN (0,1,2)
    WHERE s.id = %s
    GROUP BY s.id
    """
    return db.execute_query_one(sql, (seat_id,))
```

#### Step 2: 在 Service 层添加业务逻辑

**文件**: `service/seat_service.py`

```python
@staticmethod
def get_seat_info(seat_id):
    """获取座位详情"""
    try:
        seat = seat_dao.get_seat_detail(seat_id)
        
        if not seat:
            return {
                'success': False,
                'message': '座位不存在'
            }
        
        return {
            'success': True,
            'seat': {
                'id': seat['id'],
                'room_id': seat['room_id'],
                'room_name': seat['room_name'],
                'x': seat['x'],
                'y': seat['y'],
                'status': seat['status'],
                'recent_orders': seat['order_count']
            }
        }
    except Exception as e:
        logger.error(f"获取座位详情失败: {e}")
        return {
            'success': False,
            'message': f'获取失败: {str(e)}'
        }
```

#### Step 3: 在 API 层添加路由

**文件**: `api/seat.py`

```python
@seat_bp.route('/seats/<int:seat_id>', methods=['GET'])
def get_seat(seat_id):
    """获取座位详情"""
    try:
        result = seat_service.get_seat_info(seat_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
    
    except Exception as e:
        logger.error(f"获取座位错误: {e}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500
```

#### 完成！现在可以访问：
```
GET /api/seats/1
```

---

## 常用命令

### 数据库命令

```bash
# 连接数据库
mysql -u root -p school

# 查看表结构
DESC orders;
DESC seat;

# 查看订单列表
SELECT * FROM orders;

# 清空表（开发测试用）
DELETE FROM orders;
TRUNCATE TABLE orders;

# 查看索引
SHOW INDEX FROM orders;
```

### Python 命令

```bash
# 查看已安装的包
pip list

# 更新依赖
pip install -r requirements.txt --upgrade

# 生成依赖列表
pip freeze > requirements.txt
```

### Git 命令

```bash
# 初始化 Git
git init

# 查看状态
git status

# 添加文件
git add .

# 提交
git commit -m "feat: 初始化项目架构"

# 查看日志
git log --oneline
```

---

## 故障排查

### ❌ 错误 1：数据库连接失败

```
Error: (2003, "Can't connect to MySQL server on 'localhost' (10061)")
```

**解决**：
1. 确保 MySQL 服务已启动
2. 检查 `config.py` 中的 host/user/password
3. 创建数据库 `school`

### ❌ 错误 2：模块导入失败

```
ModuleNotFoundError: No module named 'utils'
```

**解决**：
1. 确保在项目根目录运行 `python app.py`
2. 确保 `utils/__init__.py` 存在

### ❌ 错误 3：事务锁超时

```
Error: (1205, 'Lock wait timeout exceeded')
```

**解决**：
1. 检查是否有长时间持有锁的操作
2. 调整 MySQL 配置：`SET innodb_lock_wait_timeout = 50`

### ❌ 错误 4：时间格式错误

```
ValueError: time data '2024-05-06T09:00:00' does not match format '%Y-%m-%d %H:%M:%S'
```

**解决**：
使用标准 ISO 格式或在 Service 层统一转换

---

## 📝 开发检查清单

完成每个新功能前，检查以下项目：

- [ ] DAO 层：编写 SQL 查询和更新
- [ ] Service 层：添加业务逻辑和参数验证
- [ ] API 层：添加路由和请求验证
- [ ] 日志：添加适当的日志输出
- [ ] 异常处理：处理所有可能的异常
- [ ] 测试：用 curl/Postman 测试接口
- [ ] 文档：更新接口文档

---

## 🎯 建议的开发顺序

1. **第1周**：搭建架构、数据库初始化
2. **第2周**：开发座位模块（init + query）
3. **第3周**：开发订单模块（预约 + 双重校验）
4. **第4周**：开发管理端、定时任务、联调
5. **第5周**：测试、优化、部署

---

## 📚 参考资源

- Flask 官方文档：https://flask.palletsprojects.com/
- MySQL 官方文档：https://dev.mysql.com/doc/
- APScheduler：https://apscheduler.readthedocs.io/
- PyMySQL：https://pymysql.readthedocs.io/

---

💡 **小贴士**：
- 定期备份数据库：`mysqldump -u root -p school > backup.sql`
- 使用 Postman 或 Insomnia 测试 API
- 在 Service 层写单元测试会节省大量调试时间
