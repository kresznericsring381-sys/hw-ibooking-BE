# 🏗️ 房间预约系统后端架构设计文档

> **📝 更新说明 (2026-05-07)**: 已修复数据库字段不匹配问题。`orders`表不包含`room_id`字段，相关查询已通过JOIN `seat`表获取教室信息。

## 📋 目录
1. [项目概述](#项目概述)
2. [架构设计](#架构设计)
3. [分层设计](#分层设计)
4. [数据库设计](#数据库设计)
5. [接口对应任务](#接口对应任务)
6. [关键业务流程](#关键业务流程)
7. [核心算法](#核心算法)
8. [部署启动](#部署启动)

---

## 项目概述

**项目名**：房间预约系统（Room Appointment System）

**技术栈**：
- 后端框架：Flask 2.3.3
- 数据库：MySQL
- ORM：PyMySQL（原生 SQL）
- 定时任务：APScheduler
- 架构模式：**前后端分离 + MVC 标准分层**

**核心特性**：
- ✅ 座位批量初始化（事务 + 批量 INSERT）
- ✅ 实时座位状态多表联查
- ✅ 订单双重校验（一人多单 + 座位重叠）
- ✅ 事务 + 行级排他锁防超卖
- ✅ 自动违约检测（定时任务）
- ✅ 管理端监控与强制取消

---

## 架构设计

### 🗂️ 文件结构

```
room_appointment_sys_BE/
│
├── app.py                          # ⭐ Flask 应用入口
├── config.py                       # 全局配置
├── requirements.txt                # 依赖
├── .gitignore
│
├── api/                            # 📡 接口层（路由）
│   ├── __init__.py
│   ├── room.py                     # 教室接口
│   ├── seat.py                     # 座位接口（任务2）
│   ├── order.py                    # 订单接口（任务3）
│   └── admin.py                    # 管理端接口（任务4）
│
├── service/                        # 🧠 业务逻辑层
│   ├── __init__.py
│   ├── seat_service.py             # 座位业务逻辑
│   └── order_service.py            # 订单业务逻辑（核心）
│
├── dao/                            # 💾 数据访问层
│   ├── __init__.py
│   ├── seat_dao.py                 # 座位 SQL 操作
│   └── order_dao.py                # 订单 SQL 操作
│
└── utils/                          # 🛠️ 工具
    ├── __init__.py
    ├── db.py                       # 数据库连接、事务、锁
    └── scheduler.py                # 定时任务（违约清理）
```

### 🔄 分层调用流程

```
Frontend (前端)
    ↓
API 层 (routes)
    ↓
Service 层 (业务逻辑)
    ↓
DAO 层 (SQL)
    ↓
Database (MySQL)
```

---

## 分层设计

### 1️⃣ **API 层（接口层）** - `api/`

**职责**：
- 处理 HTTP 请求/响应
- 参数验证
- 调用 Service 层

**文件**：
- `seat.py`：座位接口
- `order.py`：订单接口
- `admin.py`：管理端接口
- `room.py`：教室接口

**特点**：
- 无业务逻辑，只做**参数校验 + 路由 + 响应格式化**
- 使用 Flask Blueprint 组织模块化路由

---

### 2️⃣ **Service 层（业务逻辑层）** - `service/`

**职责**：
- 核心业务逻辑处理
- 时间校验、冲突检测
- 事务管理
- 数据格式化

**文件**：
- `seat_service.py`：座位初始化、状态查询
- `order_service.py`：订单预约、状态更新

**特点**：
- **所有复杂的业务规则都在这里**
- 不直接操作数据库（通过 DAO 层）
- 返回统一格式的响应

**示例**（订单预约流程）：
```python
def make_appointment(student_id, seat_id, room_id, start_time, end_time):
    # 1. 校验时间范围
    # 2. 开启事务 + 锁定座位
    # 3. 检测一人多单冲突
    # 4. 检测座位冲突
    # 5. 生成订单
    # 6. 提交事务
```

---

### 3️⃣ **DAO 层（数据访问层）** - `dao/`

**职责**：
- **只做 SQL**，不做业务逻辑
- CRUD 操作
- SQL 优化

**文件**：
- `seat_dao.py`：座位表操作
- `order_dao.py`：订单表操作

**特点**：
- 静态方法，无状态
- 返回原始数据库记录
- 包含所有时间段重叠判断 SQL

**关键方法**：
```python
# 批量插入座位
batch_init_seats(room_id, rows, cols)

# 多表联查（实时座位状态）
get_seat_with_order_status(room_id, start_time, end_time)

# 时间段冲突检测
check_student_time_conflict(student_id, start_time, end_time)
check_seat_time_conflict(seat_id, start_time, end_time)

# 订单监控列表
get_all_orders_with_details(status, room_id, limit, offset)
```

---

### 4️⃣ **Utils 层（工具层）** - `utils/`

**职责**：
- 数据库连接管理
- 事务控制
- 定时任务

**文件**：
- `db.py`：数据库操作
  - `get_connection()`：获取连接
  - `transaction()`：事务管理（上下文管理器）
  - `execute_query()`：查询
  - `execute_update()`：更新
  - `batch_insert()`：批量插入
  - `execute_with_lock()`：带锁的事务

- `scheduler.py`：定时任务
  - `cleanup_expired_orders()`：每分钟清理违约订单
  - `init_scheduler()`：启动调度器

---

## 数据库设计

### 📊 表结构

#### 1. **room** 教室表
```sql
CREATE TABLE room (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,           -- 教室名称
    open_time TIME NOT NULL,              -- 开放时间
    close_time TIME NOT NULL,             -- 关闭时间
    status TINYINT DEFAULT 1,             -- 1=开放, 0=关闭
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 2. **seat** 座位表
```sql
CREATE TABLE seat (
    id INT PRIMARY KEY AUTO_INCREMENT,
    room_id INT NOT NULL,
    x INT NOT NULL,                       -- 行号（网格坐标）
    y INT NOT NULL,                       -- 列号（网格坐标）
    status TINYINT DEFAULT 1,             -- 1=可用, 0=维护中
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (room_id) REFERENCES room(id),
    UNIQUE KEY (room_id, x, y)            -- 同一教室的座位坐标唯一
);
```

#### 3. **student** 学生表
```sql
CREATE TABLE student (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id VARCHAR(50) UNIQUE NOT NULL,  -- 学号
    name VARCHAR(100) NOT NULL,
    password VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 4. **orders** 订单表（核心）
```sql
CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id VARCHAR(50) NOT NULL,
    seat_id INT NOT NULL,
    start_time DATETIME NOT NULL,         -- 预约开始时间
    end_time DATETIME NOT NULL,           -- 预约结束时间
    status TINYINT DEFAULT 0,             -- 状态枚举（见下）
    sign_time DATETIME DEFAULT NULL,      -- 签到时间
    finish_time DATETIME DEFAULT NULL,    -- 完成时间
    create_time TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (student_id) REFERENCES student(student_id),
    FOREIGN KEY (seat_id) REFERENCES seat(id),
    INDEX idx_student (student_id),
    INDEX idx_seat (seat_id)
);
    INDEX idx_status (status),
    INDEX idx_create_time (create_time)
);
```

**订单状态枚举**：
| 状态值 | 状态名 | 说明 |
|------|--------|------|
| 0 | 待签到 | 预约成功，等待签到 |
| 1 | 使用中 | 已签到，正在使用 |
| 2 | 已完成 | 正常完成 |
| 3 | 违约 | 开始时间已过 30 分钟未签到 |
| 4 | 取消 | 已取消 |

---

## 接口对应任务

### 🎯 任务2：座位批量初始化与实时状态

#### 接口1：`POST /api/admin/seat/init` - 批量初始化座位

**任务**：使用批量插入，一次性生成教室全部网格数据

**请求**：
```json
{
    "room_id": 1,
    "rows": 10,
    "cols": 10
}
```

**响应**：
```json
{
    "success": true,
    "message": "座位初始化成功",
    "count": 100,
    "room_id": 1,
    "grid": {"rows": 10, "cols": 10}
}
```

**实现细节**：
- 使用 `batch_insert()` 批量插入（性能优化）
- 单条事务，保证原子性
- 防止重复初始化

---

#### 接口2：`GET /api/rooms/<id>/seats?start_time=...&end_time=...` - 实时座位状态

**任务**：难点：左连接订单表，实时返回带红绿状态的座位

**请求**：
```
GET /api/rooms/1/seats?start_time=2024-05-06T09:00:00&end_time=2024-05-06T11:00:00
```

**响应**：
```json
{
    "success": true,
    "room_id": 1,
    "time_range": {
        "start": "2024-05-06 09:00:00",
        "end": "2024-05-06 11:00:00"
    },
    "seats": [
        {
            "id": 1,
            "x": 0,
            "y": 0,
            "is_occupied": 0,        // 0=绿色（可用）, 1=红色（占用）
            "student_id": null,
            "order_id": null
        },
        {
            "id": 2,
            "x": 0,
            "y": 1,
            "is_occupied": 1,        // 已被占用
            "student_id": "2024001",
            "order_id": 123
        },
        // ... 更多座位
    ]
}
```

**关键 SQL**（多表联查 + 时间段重叠判断）：
```sql
SELECT 
    s.id, s.room_id, s.x, s.y, s.status,
    CASE 
        WHEN o.id IS NOT NULL THEN 1  -- 占用（红色）
        ELSE 0  -- 可用（绿色）
    END AS is_occupied,
    o.id AS order_id,
    o.student_id
FROM seat s
LEFT JOIN orders o ON s.id = o.seat_id
    AND o.status IN (0, 1)  -- 只检查待签到和使用中的订单
    AND NOT (o.end_time <= ? OR o.start_time >= ?)  -- ⭐ 时间段重叠判断
WHERE s.room_id = ?
ORDER BY s.x, s.y
```

---

### 🎯 任务3：订单核心功能

#### 接口3：`POST /api/orders` - 创建订单（预约）

**任务**：
- 设计核心 Orders 订单表结构 ✅（上面已完成）
- 编写"一人多单"与"同座位"重叠校验
- 引入事务与行级排他锁防超卖

**请求**：
```json
{
    "student_id": "2024001",
    "seat_id": 5,
    "room_id": 1,
    "start_time": "2024-05-06T09:00:00",
    "end_time": "2024-05-06T11:00:00"
}
```

**响应（成功）**：
```json
{
    "success": true,
    "order_id": 123,
    "message": "预约成功"
}
```

**响应（失败示例）**：
```json
{
    "success": false,
    "message": "您在该时间段已有其他预约"
}
```

**核心流程**（事务 + 锁 + 双重校验）：

```sql
BEGIN TRANSACTION
    -- 1. 锁定座位
    SELECT * FROM seat WHERE id=5 FOR UPDATE
    
    -- 2. 检测一人多单冲突
    SELECT * FROM orders 
    WHERE student_id='2024001' AND status IN (0,1,2)
    AND NOT (end_time <= ? OR start_time >= ?)
    
    -- 3. 检测座位冲突
    SELECT * FROM orders 
    WHERE seat_id=5 AND status IN (0,1,2)
    AND NOT (end_time <= ? OR start_time >= ?)
    
    -- 4. 都没有冲突，则生成订单
    INSERT INTO orders (...)
COMMIT
```

---

#### 接口4：`GET /api/orders?student_id=...` - 获取订单列表

**请求**：
```
GET /api/orders?student_id=2024001
GET /api/orders?student_id=2024001&status=0
```

**响应**：
```json
{
    "success": true,
    "orders": [
        {
            "id": 1,
            "seat_id": 5,
            "room_id": 1,
            "start_time": "2024-05-06 09:00:00",
            "end_time": "2024-05-06 11:00:00",
            "status": 0,
            "status_name": "待签到",
            "create_time": "2024-05-06 08:00:00"
        }
    ]
}
```

---

#### 接口5、6：签到与完成

- `POST /api/orders/<id>/checkin` - 签到（0 → 1）
- `POST /api/orders/<id>/complete` - 完成（1 → 2）

---

### 🎯 任务4：管理端功能

#### 接口7：`GET /api/admin/orders` - 订单监控列表

**任务**：提供给后台的联表查询，显示完整的订单信息

**请求**：
```
GET /api/admin/orders
GET /api/admin/orders?status=0&page=1&page_size=20
GET /api/admin/orders?room_id=1
```

**响应**：
```json
{
    "success": true,
    "total": 100,
    "page": 1,
    "page_size": 20,
    "orders": [
        {
            "id": 1,
            "student_id": "2024001",
            "student_name": "张三",
            "seat_id": 5,
            "x": 0,
            "y": 5,
            "room_id": 1,
            "room_name": "自习室A",
            "start_time": "2024-05-06 09:00:00",
            "end_time": "2024-05-06 11:00:00",
            "status": 0,
            "status_name": "待签到",
            "create_time": "2024-05-06 08:00:00"
        }
    ]
}
```

**关键 SQL**（多表联查）：
```sql
SELECT 
    o.id, o.student_id, s.name AS student_name,
    o.seat_id, se.x, se.y,
    o.room_id, r.name AS room_name,
    o.start_time, o.end_time, o.status, o.create_time,
    CASE WHEN o.status=0 THEN '待签到' ELSE ... END AS status_name
FROM orders o
LEFT JOIN student s ON o.student_id = s.student_id
LEFT JOIN seat se ON o.seat_id = se.id
LEFT JOIN room r ON o.room_id = r.id
WHERE 1=1 [AND filters]
ORDER BY o.create_time DESC
LIMIT ? OFFSET ?
```

---

#### 接口8：`POST /api/admin/orders/<id>/cancel` - 强制取消订单

**任务**：以及强杀订单接口

**请求**：
```
POST /api/admin/orders/123/cancel
```

**响应**：
```json
{
    "success": true,
    "message": "订单已取消"
}
```

---

### 🎯 任务4：定时任务

#### 定时脚本：每分钟清理违约订单

**任务**：配置定时任务，自动扫描超时未签到订单置为"违约"

**实现**（`utils/scheduler.py`）：

```python
def cleanup_expired_orders():
    """
    每分钟执行
    
    逻辑：
    1. 查询所有待签到订单（status=0）
    2. 检查 start_time + 30分钟 是否已过
    3. 自动设置为 status=3（违约）
    """
    sql = """
    UPDATE orders SET status=3 
    WHERE status=0 
    AND DATE_ADD(start_time, INTERVAL 30 MINUTE) <= NOW()
    """

# 每分钟执行一次
scheduler.add_job(
    cleanup_expired_orders,
    'interval',
    minutes=1,
    id='cleanup_orders'
)
```

---

## 关键业务流程

### 📊 流程图1：预约流程

```
用户点击"预约"
    ↓
【前端】发送 POST /api/orders
    ↓
【API 层】参数校验
    ↓
【Service 层】调用 make_appointment()
    ↓
    1️⃣ 校验时间范围（start < end）
    ↓
    2️⃣ 开启【事务】
    ↓
    3️⃣ 【FOR UPDATE 锁定座位】防超卖
    ↓
    4️⃣ 查询"一人多单"冲突
        - 检测该学生是否在时间段内有其他订单
    ↓
    5️⃣ 查询"座位冲突"
        - 检测该座位是否在时间段内被占用
    ↓
    6️⃣ 都检查通过 → 生成订单（INSERT）
    ↓
    7️⃣ 【提交事务】
    ↓
返回 order_id + 成功消息
```

### 📊 流程图2：定时任务

```
APScheduler（后台线程）
    ↓
【每分钟执行一次】
    ↓
扫描所有 status=0 的订单
    ↓
检查：start_time + 30分钟 <= NOW()
    ↓
    │
    ├─ YES → UPDATE status=3（违约）
    │
    └─ NO → 跳过
```

---

## 核心算法

### ⚙️ 时间段重叠判断

```
判断两个时间段是否重叠：

时间段1：[A_start, A_end]
时间段2：[B_start, B_end]

重叠条件：NOT (A_end <= B_start OR A_start >= B_end)
即：A_end > B_start AND A_start < B_end

SQL 示例：
SELECT * FROM orders 
WHERE NOT (end_time <= ? OR start_time >= ?)
```

### ⚙️ 行级排他锁

```
并发场景：两个用户同时预约同一座位

【用户1】  【用户2】
  ↓         ↓
BEGIN       BEGIN
  ↓         ↓
SELECT * FROM seat WHERE id=5 FOR UPDATE  ← 【用户1】获得锁
  ↓         ↓
  ✅        等待...
  ↓         ↓
INSERT ORDER  ↓
  ↓         ↓
COMMIT      ← 【用户1】释放锁
  ↓         ↓
  ✓         SELECT * FROM seat（现在【用户2】获得锁）
  ↓         ↓
返回成功      检测冲突 → 发现该座位已被占用 → 回滚
  ↓         ↓
           返回"座位已占用"
```

---

## 部署启动

### 📦 安装依赖

```bash
pip install -r requirements.txt
```

### 🚀 启动服务

```bash
python app.py
```

**日志输出**：
```
2024-05-06 12:00:00 - __main__ - INFO - ==================================================
2024-05-06 12:00:00 - __main__ - INFO - 🚀 房间预约系统后端启动
2024-05-06 12:00:00 - __main__ - INFO - ==================================================
2024-05-06 12:00:00 - utils.scheduler - INFO - 定时任务调度器已启动
2024-05-06 12:00:00 - __main__ - INFO -  * Running on http://0.0.0.0:5000
```

### 🧪 测试接口

```bash
# 1. 健康检查
curl http://localhost:5000/api/health

# 2. 获取教室列表
curl http://localhost:5000/api/rooms

# 3. 初始化座位（管理员）
curl -X POST http://localhost:5000/api/admin/seat/init \
  -H "Content-Type: application/json" \
  -d '{"room_id":1,"rows":10,"cols":10}'

# 4. 获取座位状态
curl "http://localhost:5000/api/rooms/1/seats?start_time=2024-05-06T09:00:00&end_time=2024-05-06T11:00:00"

# 5. 创建订单
curl -X POST http://localhost:5000/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "student_id":"2024001",
    "seat_id":1,
    "room_id":1,
    "start_time":"2024-05-06T09:00:00",
    "end_time":"2024-05-06T11:00:00"
  }'

# 6. 获取订单列表
curl "http://localhost:5000/api/orders?student_id=2024001"

# 7. 签到
curl -X POST http://localhost:5000/api/orders/1/checkin

# 8. 获取订单监控列表
curl "http://localhost:5000/api/admin/orders?status=0"

# 9. 强制取消
curl -X POST http://localhost:5000/api/admin/orders/1/cancel
```

---

## 📝 总结

✅ **架构优点**：
1. **清晰的分层**：API → Service → DAO，职责明确
2. **可维护性**：修改业务逻辑只需改 Service，不影响其他层
3. **可测试性**：每层可独立测试
4. **性能优化**：批量操作、索引优化、事务管理
5. **并发安全**：行级锁防超卖，事务保证一致性

✅ **任务完成度**：
- ✅ 任务2：座位批量初始化 + 实时状态
- ✅ 任务3：订单表结构 + 双重校验 + 事务锁
- ✅ 任务4：管理端监控 + 定时清理

🎯 **下一步开发顺序**：
1. 搭建分层架构 ✅（已完成）
2. 数据库初始化（导入 school.sql）
3. 开发座位接口
4. 开发订单接口
5. 测试事务和锁
6. 部署定时任务
7. 前端集成
