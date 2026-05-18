# ================== 座位 DAO 层 ==================
"""
seat_dao.py - 座位数据访问层（只做 SQL）

职责：
1. 座位批量插入
2. 座位查询
3. 座位状态更新
"""

from utils.db import db, batch_insert
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SeatDAO:
    """座位数据访问类"""
    
    @staticmethod
    def batch_init_seats(room_id, rows, cols):
        """
        批量初始化座位（任务二）
        
        参数：
        - room_id: 教室 ID
        - rows: 行数
        - cols: 列数
        
        返回：插入的座位数
        """
        data_list = []
        for x in range(rows):
            for y in range(cols):
                data_list.append((room_id, x, y, 1))  # status=1 表示可用
        
        columns = ['room_id', 'x', 'y', 'status']
        return batch_insert('seat', columns, data_list)
    
    @staticmethod
    def get_seats_by_room(room_id):
        """
        获取教室的所有座位
        
        返回：座位列表
        """
        sql = "SELECT * FROM seat WHERE room_id=%s ORDER BY x, y"
        return db.execute_query(sql, (room_id,))
    
    @staticmethod
    def get_seat_with_order_status(room_id, start_time, end_time):
        """
        【任务二】实时座位状态多表联查（难点）
        
        LEFT JOIN orders 表，返回带有红/绿状态的座位
        
        参数：
        - room_id: 教室 ID
        - start_time: 查询的开始时间
        - end_time: 查询的结束时间
        
        返回：座位列表（包含是否被占用的信息）
        
        逻辑：
        - 如果有订单覆盖时间段 → 红色（占用）
        - 否则 → 绿色（可用）
        """
        sql = """
        SELECT 
            s.id,
            s.room_id,
            s.x,
            s.y,
            s.status,
            CASE 
                WHEN o.id IS NOT NULL THEN 1  -- 1=占用（红色）
                ELSE 0  -- 0=可用（绿色）
            END AS is_occupied,
            o.id AS order_id,
            o.student_id,
            o.status AS order_status
        FROM seat s
        LEFT JOIN orders o ON s.id = o.seat_id
            AND o.status IN (0, 1)  -- 0=待签到, 1=使用中
            AND NOT (o.end_time <= %s OR o.start_time >= %s)  -- 时间段重叠判断
        WHERE s.room_id = %s
        ORDER BY s.x, s.y
        """
        return db.execute_query(sql, (start_time, end_time, room_id))
    
    @staticmethod
    def get_seat_by_id(seat_id):
        """
        根据座位 ID 获取座位信息
        
        用途：在订单前验证座位存在性
        """
        sql = "SELECT * FROM seat WHERE id=%s"
        return db.execute_query_one(sql, (seat_id,))
    
    @staticmethod
    def lock_seat(seat_id):
        """
        【任务三】行级排他锁 - 锁定座位
        
        用于事务中，防止并发超卖
        
        返回：座位记录
        """
        sql = "SELECT * FROM seat WHERE id=%s FOR UPDATE"
        # 注：这个函数需要在事务中调用，否则无效
        return db.execute_query_one(sql, (seat_id,))
    
    @staticmethod
    def update_seat_status(seat_id, status):
        """
        更新座位状态
        
        参数：
        - seat_id: 座位 ID
        - status: 0=占用, 1=可用
        """
        sql = "UPDATE seat SET status=%s WHERE id=%s"
        return db.execute_update(sql, (status, seat_id))


# 全局实例
seat_dao = SeatDAO()
