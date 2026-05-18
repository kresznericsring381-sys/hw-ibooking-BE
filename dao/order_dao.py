# ================== 订单 DAO 层 ==================
"""
order_dao.py - 订单数据访问层（只做 SQL）

职责：
1. 订单创建（插入）
2. 订单查询（单个、列表、时间段冲突检测）
3. 订单状态更新
4. 订单删除/取消

注意：所有与时间段重叠相关的判断都在这里实现
"""

from utils.db import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrderDAO:
    """订单数据访问类"""
    
    # ============ 订单状态枚举 ============
    STATUS_PENDING = 0       # 待签到
    STATUS_IN_USE = 1        # 使用中
    STATUS_COMPLETED = 2     # 已完成
    STATUS_VIOLATED = 3      # 违约
    STATUS_CANCELLED = 4     # 取消
    
    STATUS_MAP = {
        0: '待签到',
        1: '使用中',
        2: '已完成',
        3: '违约',
        4: '取消'
    }
    
    @staticmethod
    def create_order(student_id, seat_id, start_time, end_time):
        """
        创建订单
        
        参数：
        - student_id: 学生学号
        - seat_id: 座位 ID
        - start_time: 预约开始时间 (datetime)
        - end_time: 预约结束时间 (datetime)
        
        返回：订单 ID 或 None
        """
        sql = """
        INSERT INTO orders 
        (student_id, seat_id, start_time, end_time, status, create_time)
        VALUES (%s, %s, %s, %s, %s, NOW())
        """
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, (
                student_id, seat_id, 
                start_time, end_time, 
                OrderDAO.STATUS_PENDING
            ))
            conn.commit()
            order_id = cursor.lastrowid
            logger.info(f"订单创建成功: {order_id}")
            return order_id
        except Exception as e:
            conn.rollback()
            logger.error(f"创建订单失败: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def check_student_time_conflict(student_id, start_time, end_time):
        """
        【任务三】检测 - 一人多单冲突
        
        检查某个学生在给定时间段是否已有其他订单
        
        参数：
        - student_id: 学生学号
        - start_time: 查询的开始时间
        - end_time: 查询的结束时间
        
        返回：冲突的订单列表（如果为空则无冲突）
        
        SQL 时间段重叠判断：
        NOT (order.end_time <= start_time OR order.start_time >= end_time)
        """
        sql = """
        SELECT id, seat_id, start_time, end_time, status 
        FROM orders 
        WHERE student_id = %s
        AND status IN (0, 1, 2)  -- 排除已取消和违约的订单
        AND NOT (end_time <= %s OR start_time >= %s)
        """
        return db.execute_query(sql, (student_id, start_time, end_time))
    
    @staticmethod
    def check_seat_time_conflict(seat_id, start_time, end_time):
        """
        【任务三】检测 - 同座位重叠冲突
        
        检查某个座位在给定时间段是否已被预约
        
        参数：
        - seat_id: 座位 ID
        - start_time: 查询的开始时间
        - end_time: 查询的结束时间
        
        返回：冲突的订单列表（如果为空则无冲突）
        """
        sql = """
        SELECT id, student_id, start_time, end_time, status 
        FROM orders 
        WHERE seat_id = %s
        AND status IN (0, 1, 2)  -- 排除已取消和违约的订单
        AND NOT (end_time <= %s OR start_time >= %s)
        """
        return db.execute_query(sql, (seat_id, start_time, end_time))
    
    @staticmethod
    def get_order_by_id(order_id):
        """
        根据订单 ID 获取订单信息
        
        返回：订单记录
        """
        sql = """
        SELECT o.*, s.name AS student_name, r.name AS room_name, 
               se.x, se.y, se.room_id
        FROM orders o
        LEFT JOIN student s ON o.student_id = s.student_id
        LEFT JOIN seat se ON o.seat_id = se.id
        LEFT JOIN room r ON se.room_id = r.id
        WHERE o.id = %s
        """
        return db.execute_query_one(sql, (order_id,))
    
    @staticmethod
    def get_orders_by_student(student_id, status=None, limit=None):
        """
        获取学生的订单列表
        
        参数：
        - student_id: 学生学号
        - status: 订单状态（可选），None 表示所有状态
        - limit: 限制条数（可选）
        
        返回：订单列表
        """
        sql = """
        SELECT o.*, se.room_id, se.x, se.y
        FROM orders o
        LEFT JOIN seat se ON o.seat_id = se.id
        WHERE o.student_id = %s
        """
        params = [student_id]
        
        if status is not None:
            sql += " AND o.status = %s"
            params.append(status)
        
        sql += " ORDER BY o.create_time DESC"
        
        if limit:
            sql += " LIMIT %s"
            params.append(limit)
        
        return db.execute_query(sql, params)
    
    @staticmethod
    def get_all_orders_with_details(status=None, room_id=None, limit=100, offset=0):
        """
        【任务四】获取订单监控列表（多表联查）
        
        用于管理端，返回完整的订单信息（学生名、座位号、教室名等）
        
        参数：
        - status: 订单状态（可选）
        - room_id: 教室 ID（可选）
        - limit: 分页限制
        - offset: 分页偏移
        
        返回：订单列表（包含学生、座位、教室详细信息）
        """
        sql = """
        SELECT 
            o.id,
            o.student_id,
            s.name AS student_name,
            o.seat_id,
            se.x,
            se.y,
            se.room_id,
            r.name AS room_name,
            o.start_time,
            o.end_time,
            o.status,
            o.create_time,
            CASE 
                WHEN o.status = 0 THEN '待签到'
                WHEN o.status = 1 THEN '使用中'
                WHEN o.status = 2 THEN '已完成'
                WHEN o.status = 3 THEN '违约'
                WHEN o.status = 4 THEN '取消'
            END AS status_name
        FROM orders o
        LEFT JOIN student s ON o.student_id = s.student_id
        LEFT JOIN seat se ON o.seat_id = se.id
        LEFT JOIN room r ON se.room_id = r.id
        WHERE 1=1
        """
        
        params = []
        
        if status is not None:
            sql += " AND o.status = %s"
            params.append(status)
        
        if room_id is not None:
            sql += " AND se.room_id = %s"
            params.append(room_id)
        
        sql += " ORDER BY o.create_time DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        return db.execute_query(sql, params)
    
    @staticmethod
    def update_order_status(order_id, new_status):
        """
        更新订单状态
        
        参数：
        - order_id: 订单 ID
        - new_status: 新状态
        
        返回：受影响行数
        """
        sql = "UPDATE orders SET status=%s WHERE id=%s"
        return db.execute_update(sql, (new_status, order_id))
    
    @staticmethod
    def cancel_order(order_id):
        """
        【任务四】强制取消订单
        
        将订单状态改为 4（取消）
        
        参数：
        - order_id: 订单 ID
        
        返回：受影响行数
        """
        sql = "UPDATE orders SET status=%s WHERE id=%s"
        return db.execute_update(sql, (OrderDAO.STATUS_CANCELLED, order_id))
    
    @staticmethod
    def check_in_order(order_id):
        """
        签到订单
        
        状态 0（待签到）→ 1（使用中）
        
        参数：
        - order_id: 订单 ID
        
        返回：受影响行数
        """
        sql = "UPDATE orders SET status=%s WHERE id=%s AND status=%s"
        return db.execute_update(sql, (
            OrderDAO.STATUS_IN_USE,
            order_id,
            OrderDAO.STATUS_PENDING
        ))
    
    @staticmethod
    def complete_order(order_id):
        """
        完成订单
        
        状态 1（使用中）→ 2（已完成）
        
        参数：
        - order_id: 订单 ID
        
        返回：受影响行数
        """
        sql = "UPDATE orders SET status=%s WHERE id=%s AND status=%s"
        return db.execute_update(sql, (
            OrderDAO.STATUS_COMPLETED,
            order_id,
            OrderDAO.STATUS_IN_USE
        ))


# 全局实例
order_dao = OrderDAO()
