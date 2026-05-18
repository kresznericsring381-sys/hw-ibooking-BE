# 📊 项目架构总结表

> **📝 更新说明 (2026-05-07)**: 已修复数据库字段不匹配问题。`orders`表不包含`room_id`字段，相关查询已通过JOIN `seat`表获取教室信息。

## 🏗️ 分层架构速览

| 层级 | 目录 | 文件 | 职责 | 示例方法 |
|------|------|------|------|---------|
| **API 层** | `api/` | `seat.py` | 处理 HTTP 请求 | `/api/admin/seat/init` |
| | | `order.py` | 订单预约接口 | `/api/orders` |
| | | `admin.py` | 管理端接口 | `/api/admin/orders` |
| | | `room.py` | 教室查询接口 | `/api/rooms` |
| **Service 层** | `service/` | `seat_service.py` | 座位业务逻辑 | `init_room_seats()` |
| | | `order_service.py` | 订单业务逻辑 | `make_appointment()` |
| **DAO 层** | `dao/` | `seat_dao.py` | 座位数据操作 | `batch_init_seats()` |
| | | `order_dao.py` | 订单数据操作 | `check_student_time_conflict()` |
| **Utils 层** | `utils/` | `db.py` | 数据库连接、事务 | `execute_with_lock()` |
| | | `scheduler.py` | 定时任务 | `cleanup_expired_orders()` |
| **配置层** | - | `config.py` | 全局配置 | `DB_CONFIG` |
| **入口** | - | `app.py` | Flask 应用启动 | `if __name__ == '__main__'` |

---

## 📡 API 接口路由表

### 学生端接口

| HTTP | 接口 | 描述 | 任务 |
|------|------|------|------|
| POST | `/api/login` | 登录 | 基础 |
| POST | `/api/register` | 注册 | 基础 |
| GET | `/api/rooms` | 获取教室列表 | 基础 |
| GET | `/api/rooms/<id>/seats` | 📍 实时座位状态 | **任务2** |
| POST | `/api/orders` | 📍 创建订单（预约） | **任务3** |
| GET | `/api/orders` | 📍 获取我的订单 | **任务3** |
| POST | `/api/orders/<id>/checkin` | 签到 | **任务3** |
| POST | `/api/orders/<id>/complete` | 完成 | **任务3** |

### 管理端接口

| HTTP | 接口 | 描述 | 任务 |
|------|------|------|------|
| POST | `/api/admin/seat/init` | 📍 批量初始化座位 | **任务2** |
| GET | `/api/admin/orders` | 📍 订单监控列表 | **任务4** |
| POST | `/api/admin/orders/<id>/cancel` | 📍 强制取消订单 | **任务4** |
| GET | `/api/admin/dashboard` | 数据统计 | 扩展 |

---

## 🗄️ 数据库表关系图

```
┌──────────────────────────────────────────────────┐
│                   room（教室）                      │
│  id, name, open_time, close_time, status       │
└────────────────────┬─────────────────────────────┘
                     │
            ┌────────┴─────────┐
            │                  │
            ▼                  ▼
      ┌──────────────┐  ┌────────────────────┐
      │ seat（座位）   │  │ orders（订单）      │
      │ id, room_id  │  │ id, seat_id        │
      │ x, y, status │  │ student_id         │
      └──────────────┘  │ start_time         │
                        │ end_time           │
                        │ status             │
                        └────────────────────┘
                             △
                             │
                        ┌────┴────┐
                        │          │
                   ┌────────────┐  │
                   │student     │  │
                   │id          │  │
                   │student_id  │◄─┘
                   │name        │
                   │password    │
                   └────────────┘
```

---

## 🔑 核心算法速记

### 时间段重叠判断

```
【不重叠】         【重叠】
A ├─────┤        A ├────────┤
B     ├─────┤   B   ├────────┤

重叠条件：NOT (A.end <= B.start OR A.start >= B.end)
等于：A.end > B.start AND A.start < B.end
```

### 事务 + 锁流程

```
┌─────────────────────────────────┐
│ BEGIN TRANSACTION               │
│   1. SELECT ... FOR UPDATE      │ ← 获得行级锁
│   2. 检测学生冲突              │
│   3. 检测座位冲突              │
│   4. INSERT orders             │
│ COMMIT / ROLLBACK              │ ← 释放锁
└─────────────────────────────────┘
```

---

## 📊 订单状态转移图

```
    ┌───────────────┐
    │    预约成功    │
    │   status=0    │
    │   待签到      │
    └───────┬───────┘
            │
     ┌──────┴──────┐
     │             │
    ▼              ▼
 签到          30min未签到
   │               │
   │               ▼
   │          ┌─────────────┐
   │          │  status=3   │
   │          │    违约     │
   │          └─────────────┘
   │
   ▼
┌──────────────────┐
│  status=1        │
│  使用中          │
└────────┬─────────┘
         │
    完成操作
         │
         ▼
  ┌────────────────┐
  │  status=2      │
  │  已完成        │
  └────────────────┘

【强制取消流程】
任意状态 → status=4（取消）
```

---

## 🛠️ 关键函数索引

### DAO 层关键方法

```python
# seat_dao.py
batch_init_seats(room_id, rows, cols)           # 批量初始化座位
get_seat_with_order_status(room_id, start, end) # 实时座位状态（多表联查）
lock_seat(seat_id)                               # 行级锁

# order_dao.py
create_order(student_id, seat_id, start, end)    # 创建订单
check_student_time_conflict(student_id, s, e)   # 一人多单检测
check_seat_time_conflict(seat_id, s, e)         # 座位冲突检测
get_all_orders_with_details(...)                 # 监控列表（多表联查）
cancel_order(order_id)                           # 强制取消
```

### Service 层关键方法

```python
# seat_service.py
init_room_seats(room_id, rows, cols)             # 座位初始化流程
get_room_seats_status(room_id, start, end)       # 座位状态返回

# order_service.py
make_appointment(student_id, seat_id, ...)       # 核心预约流程（事务+锁）
validate_time_range(start, end)                  # 时间范围校验
get_student_orders(student_id, status)           # 订单列表
check_in(order_id)                               # 签到
complete(order_id)                               # 完成
```

### Utils 层关键方法

```python
# db.py
get_connection()                                  # 获取连接
transaction()                                     # 事务上下文管理器
execute_with_lock(...)                            # 带锁事务执行
batch_insert(table, columns, data_list)           # 批量插入

# scheduler.py
cleanup_expired_orders()                          # 清理违约任务
init_scheduler()                                  # 启动调度器
```

---

## 📈 性能优化清单

### 索引优化（已在 SQL 中配置）

```sql
-- orders 表关键索引
INDEX idx_student_time (student_id, start_time, end_time)  -- 学生时段查询
INDEX idx_seat_time (seat_id, start_time, end_time)        -- 座位冲突检测
INDEX idx_status (status)                                   -- 状态查询
INDEX idx_create_time (create_time)                         -- 时间序查询

-- seat 表
UNIQUE KEY (room_id, x, y)                                  -- 座位坐标唯一性
```

### 批量操作

- ✅ 座位初始化：使用 `batch_insert()`
- ✅ 订单查询：使用分页 LIMIT/OFFSET
- ✅ 状态更新：可以批量 UPDATE

### 缓存建议

- 教室列表：可缓存 1 小时
- 座位状态：实时查询（支持前端轮询）
- 定时任务：只运行 1 个线程

---

## 🔐 安全性检查清单

- [ ] 参数验证：所有输入都验证类型和范围
- [ ] SQL 注入防护：使用参数化查询（`%s` 占位符）
- [ ] 事务隔离：使用 `FOR UPDATE` 防超卖
- [ ] 密码加密：未来可添加 bcrypt/MD5
- [ ] 访问控制：API 层可添加权限检查
- [ ] 日志记录：关键操作都记录日志

---

## 📋 快速测试脚本

```bash
#!/bin/bash

# 测试所有关键接口
BASE_URL="http://localhost:5000"

echo "1. 健康检查"
curl $BASE_URL/api/health

echo "\n2. 获取教室"
curl $BASE_URL/api/rooms

echo "\n3. 初始化座位"
curl -X POST $BASE_URL/api/admin/seat/init \
  -H "Content-Type: application/json" \
  -d '{"room_id":1,"rows":10,"cols":10}'

echo "\n4. 获取座位状态"
curl "$BASE_URL/api/rooms/1/seats?start_time=2024-05-06T09:00:00&end_time=2024-05-06T11:00:00"

echo "\n5. 创建订单"
curl -X POST $BASE_URL/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "student_id":"2024001",
    "seat_id":1,
    "room_id":1,
    "start_time":"2024-05-06T09:00:00",
    "end_time":"2024-05-06T11:00:00"
  }'

echo "\n测试完成"
```

---

## 📚 文档导航

- 📖 **完整架构设计**：见 `ARCHITECTURE.md`
- 🚀 **快速开发指南**：见 `QUICK_START.md`
- 💻 **代码注释**：每个方法都有详细中文注释

---

## ✅ 项目完成度

### 架构设计：100% ✅
- [x] 分层设计完成
- [x] 所有文件生成
- [x] 关键模块实现
- [x] 详细文档编写

### 任务对应：100% ✅
- [x] 任务2：座位初始化 + 实时状态
- [x] 任务3：订单表 + 双重校验 + 事务锁
- [x] 任务4：管理端 + 定时任务

### 下一步：
- [ ] 数据库初始化
- [ ] 单元测试
- [ ] 集成测试
- [ ] 部署优化

---

**项目准备完毕，可以开始开发！** 🎉
