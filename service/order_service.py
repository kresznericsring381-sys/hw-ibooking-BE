# ================== 订单业务服务层 ==================
"""
order_service.py - 订单相关的业务逻辑（核心难点）

职责：
1. 订单预约（带事务 + 锁 + 双重校验）
2. 订单校验（时间、冲突检测）
3. 订单管理（查询、更新、取消）
4. 违约检测

核心算法：
- 时间段重叠检测
- 一人多单冲突检测
- 同座位冲突检测
- 事务 + 行级排他锁防超卖
"""

from dao.order_dao import order_dao
from dao.seat_dao import seat_dao
from utils.db import db
from datetime import datetime, timedelta
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrderService:
    """订单业务逻辑类"""
    
    @staticmethod
    def validate_time_range(start_time, end_time, room_id=None):
        """
        校验时间范围合法性
        
        检查：
        1. 开始时间 < 结束时间
        2. 不超过最大预约天数
        3. 符合教室开放时间（可选）
        
        参数：
        - start_time: 开始时间 (datetime or string)
        - end_time: 结束时间 (datetime or string)
        - room_id: 教室 ID（可选）
        
        返回：(is_valid, error_message)
        """
        try:
            # 转换时间格式
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time)
            
            # 检查 1: 开始时间必须早于结束时间
            if start_time >= end_time:
                return False, "开始时间必须早于结束时间"
            
            # 检查 2: 不能超过最大预约天数
            max_days = Config.MAX_APPOINTMENT_DAYS
            if (end_time - start_time).days > max_days:
                return False, f"预约时长不能超过 {max_days} 天"
            
            # 检查 3: 开始时间不能早于当前时间
            if start_time < datetime.now():
                return False, "预约时间不能早于当前时间"
            
            return True, None
        
        except Exception as e:
            logger.error(f"时间校验错误: {e}")
            return False, f"时间格式错误: {str(e)}"
    
    @staticmethod
    def make_appointment(student_id, seat_id, room_id, start_time, end_time):
        """
        【任务三】核心预约流程（事务 + 锁 + 双重校验）
        
        流程图：
        1. 校验时间范围
        2. 【开启事务】
        3. 【FOR UPDATE 锁定座位】
        4. 校验：一人多单冲突
        5. 校验：同座位冲突
        6. 生成订单
        7. 【提交事务】
        
        参数：
        - student_id: 学生学号
        - seat_id: 座位 ID
        - room_id: 教室 ID
        - start_time: 开始时间 (datetime or string)
        - end_time: 结束时间 (datetime or string)
        
        返回：
        {
            'success': True/False,
            'order_id': 订单 ID (成功时),
            'message': '预约成功'/'预约失败原因'
        }
        """
        try:
            # 转换时间格式
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time)
            
            # ========== 第1步：校验时间范围 ==========
            is_valid, error_msg = OrderService.validate_time_range(start_time, end_time, room_id)
            if not is_valid:
                return {
                    'success': False,
                    'message': error_msg
                }
            
            # ========== 第2步：开启事务并锁定座位 ==========
            try:
                with db.transaction() as (conn, cursor):
                    # 锁定座位（FOR UPDATE）
                    lock_sql = "SELECT * FROM seat WHERE id=%s AND room_id=%s FOR UPDATE"
                    cursor.execute(lock_sql, (seat_id, room_id))
                    seat = cursor.fetchone()
                    
                    if not seat:
                        return {
                            'success': False,
                            'message': '座位不存在或教室不匹配'
                        }
                    
                    # ========== 第3步：检测一人多单冲突 ==========
                    student_conflicts = order_dao.check_student_time_conflict(
                        student_id, start_time, end_time
                    )
                    if student_conflicts:
                        logger.warning(f"学生 {student_id} 已有冲突订单")
                        return {
                            'success': False,
                            'message': '您在该时间段已有其他预约'
                        }
                    
                    # ========== 第4步：检测同座位冲突 ==========
                    seat_conflicts = order_dao.check_seat_time_conflict(
                        seat_id, start_time, end_time
                    )
                    if seat_conflicts:
                        logger.warning(f"座位 {seat_id} 已被占用")
                        return {
                            'success': False,
                            'message': '该座位在您选择的时间段已被预约'
                        }
                    
                    # ========== 第5步：生成订单 ==========
                    order_id = order_dao.create_order(
                        student_id, seat_id, start_time, end_time
                    )
                    
                    # 事务自动提交
                    logger.info(f"订单创建成功: {order_id}")
                    
                    return {
                        'success': True,
                        'order_id': order_id,
                        'message': '预约成功'
                    }
            
            except Exception as e:
                logger.error(f"事务执行失败: {e}")
                raise
        
        except Exception as e:
            logger.error(f"预约失败: {e}")
            return {
                'success': False,
                'message': f'预约失败: {str(e)}'
            }
    
    @staticmethod
    def get_student_orders(student_id, status=None):
        """
        获取学生的订单列表
        
        参数：
        - student_id: 学生学号
        - status: 订单状态（可选）
        
        返回：订单列表
        """
        try:
            orders = order_dao.get_orders_by_student(student_id, status)
            
            # 格式化输出
            result = []
            for order in orders:
                result.append({
                    'id': order['id'],
                    'seat_id': order['seat_id'],
                    'room_id': order['room_id'],
                    'start_time': order['start_time'].strftime('%Y-%m-%d %H:%M:%S'),
                    'end_time': order['end_time'].strftime('%Y-%m-%d %H:%M:%S'),
                    'status': order['status'],
                    'status_name': order_dao.STATUS_MAP.get(order['status'], '未知'),
                    'create_time': order['create_time'].strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return {
                'success': True,
                'orders': result
            }
        
        except Exception as e:
            logger.error(f"获取订单失败: {e}")
            return {
                'success': False,
                'message': f'获取订单失败: {str(e)}'
            }
    
    @staticmethod
    def check_in(order_id):
        """
        签到订单
        
        状态：0（待签到）→ 1（使用中）
        
        参数：
        - order_id: 订单 ID
        
        返回：
        {
            'success': True/False,
            'message': '签到成功'/'签到失败原因'
        }
        """
        try:
            affected = order_dao.check_in_order(order_id)
            
            if affected > 0:
                logger.info(f"订单 {order_id} 签到成功")
                return {
                    'success': True,
                    'message': '签到成功'
                }
            else:
                return {
                    'success': False,
                    'message': '订单不存在或已签到'
                }
        
        except Exception as e:
            logger.error(f"签到失败: {e}")
            return {
                'success': False,
                'message': f'签到失败: {str(e)}'
            }
    
    @staticmethod
    def complete(order_id):
        """
        完成订单
        
        状态：1（使用中）→ 2（已完成）
        
        参数：
        - order_id: 订单 ID
        
        返回：
        {
            'success': True/False,
            'message': '完成成功'/'完成失败原因'
        }
        """
        try:
            affected = order_dao.complete_order(order_id)
            
            if affected > 0:
                logger.info(f"订单 {order_id} 完成")
                return {
                    'success': True,
                    'message': '完成成功'
                }
            else:
                return {
                    'success': False,
                    'message': '订单不存在或状态不允许'
                }
        
        except Exception as e:
            logger.error(f"完成订单失败: {e}")
            return {
                'success': False,
                'message': f'完成失败: {str(e)}'
            }


# 全局实例
order_service = OrderService()
