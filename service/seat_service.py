# ================== 座位业务服务层 ==================
"""
seat_service.py - 座位相关的业务逻辑

职责：
1. 座位初始化业务逻辑
2. 座位状态校验
3. 返回前端所需的座位视图
"""

from dao.seat_dao import seat_dao
from dao.order_dao import order_dao
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SeatService:
    """座位业务逻辑类"""
    
    @staticmethod
    def init_room_seats(room_id, rows, cols):
        """
        【任务二】座位批量初始化（事务）
        
        参数：
        - room_id: 教室 ID
        - rows: 行数
        - cols: 列数
        
        返回：
        {
            'success': True,
            'message': '初始化成功',
            'count': 100,  # 生成的座位数
            'room_id': 1,
            'grid': {'rows': 10, 'cols': 10}
        }
        """
        try:
            # 验证输入
            if rows <= 0 or cols <= 0:
                return {
                    'success': False,
                    'message': '行数和列数必须大于 0'
                }
            
            # 检查是否已初始化
            existing_seats = seat_dao.get_seats_by_room(room_id)
            if existing_seats:
                return {
                    'success': False,
                    'message': f'教室 {room_id} 已初始化过 ({len(existing_seats)} 个座位)'
                }
            
            # 批量初始化
            count = seat_dao.batch_init_seats(room_id, rows, cols)
            
            logger.info(f"教室 {room_id} 初始化完成: {rows}x{cols} = {count} 个座位")
            
            return {
                'success': True,
                'message': '座位初始化成功',
                'count': count,
                'room_id': room_id,
                'grid': {
                    'rows': rows,
                    'cols': cols
                }
            }
        
        except Exception as e:
            logger.error(f"座位初始化失败: {e}")
            return {
                'success': False,
                'message': f'初始化失败: {str(e)}'
            }
    
    @staticmethod
    def get_room_seats_status(room_id, start_time, end_time):
        """
        【任务二】获取教室座位实时状态（多表联查）
        
        返回座位的红/绿状态给前端
        
        参数：
        - room_id: 教室 ID
        - start_time: 查询的开始时间 (datetime or string)
        - end_time: 查询的结束时间 (datetime or string)
        
        返回：
        {
            'success': True,
            'room_id': 1,
            'time_range': {
                'start': '2024-05-06 09:00:00',
                'end': '2024-05-06 11:00:00'
            },
            'seats': [
                {
                    'id': 1,
                    'x': 0,
                    'y': 0,
                    'is_occupied': 0,  # 0=绿色（可用）, 1=红色（占用）
                    'student_id': None
                },
                ...
            ]
        }
        """
        try:
            # 转换时间格式
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time)
            
            # 获取座位状态
            seats = seat_dao.get_seat_with_order_status(room_id, start_time, end_time)
            
            # 构建响应格式
            seat_list = []
            for seat in seats:
                seat_list.append({
                    'id': seat['id'],
                    'x': seat['x'],
                    'y': seat['y'],
                    'is_occupied': seat['is_occupied'],  # 0=绿, 1=红
                    'student_id': seat['student_id'],
                    'order_id': seat['order_id']
                })
            
            return {
                'success': True,
                'room_id': room_id,
                'time_range': {
                    'start': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'end': end_time.strftime('%Y-%m-%d %H:%M:%S')
                },
                'seats': seat_list
            }
        
        except Exception as e:
            logger.error(f"获取座位状态失败: {e}")
            return {
                'success': False,
                'message': f'获取座位状态失败: {str(e)}'
            }


# 全局实例
seat_service = SeatService()
