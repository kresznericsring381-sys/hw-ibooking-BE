# ================== 教室接口层 ==================
"""
room.py - 教室相关的 API 接口

接口列表：
1. GET /api/rooms - 获取所有教室
2. GET /api/rooms/<id> - 获取教室详情
"""

from flask import Blueprint, request, jsonify
from utils.db import db
from datetime import timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建蓝图
room_bp = Blueprint('room', __name__, url_prefix='/api')


def format_timedelta(td):
    """将 timedelta 转换为 HH:MM:SS 格式"""
    if isinstance(td, timedelta):
        total_seconds = int(td.total_seconds())
        h = total_seconds // 3600
        m = (total_seconds % 3600) // 60
        s = total_seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
    return td


@room_bp.route('/rooms', methods=['GET'])
def get_all_rooms():
    """
    获取所有教室列表
    
    响应：
    {
        "success": true,
        "rooms": [
            {
                "id": 1,
                "name": "自习室A",
                "open_time": "09:00:00",
                "close_time": "22:00:00",
                "status": 1
            },
            ...
        ]
    }
    """
    try:
        sql = "SELECT id, name, open_time, close_time, status FROM room WHERE status=1"
        rooms = db.execute_query(sql)
        
        # 格式化时间
        result = []
        for room in rooms:
            result.append({
                'id': room['id'],
                'name': room['name'],
                'open_time': format_timedelta(room['open_time']),
                'close_time': format_timedelta(room['close_time']),
                'status': room['status']
            })
        
        return jsonify({
            'success': True,
            'rooms': result
        }), 200
    
    except Exception as e:
        logger.error(f"获取教室列表错误: {e}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@room_bp.route('/rooms/<int:room_id>', methods=['GET'])
def get_room_detail(room_id):
    """
    获取教室详情
    
    示例：
    GET /api/rooms/1
    
    响应：
    {
        "success": true,
        "room": {
            "id": 1,
            "name": "自习室A",
            "open_time": "09:00:00",
            "close_time": "22:00:00",
            "status": 1,
            "total_seats": 100,
            "available_seats": 80
        }
    }
    """
    try:
        sql = "SELECT id, name, open_time, close_time, status FROM room WHERE id=%s"
        room = db.execute_query_one(sql, (room_id,))
        
        if not room:
            return jsonify({
                'success': False,
                'message': '教室不存在'
            }), 404
        
        # 获取座位统计信息
        seat_stats = db.execute_query_one(
            "SELECT COUNT(*) as total FROM seat WHERE room_id=%s",
            (room_id,)
        )
        
        return jsonify({
            'success': True,
            'room': {
                'id': room['id'],
                'name': room['name'],
                'open_time': format_timedelta(room['open_time']),
                'close_time': format_timedelta(room['close_time']),
                'status': room['status'],
                'total_seats': seat_stats['total'] if seat_stats else 0
            }
        }), 200
    
    except Exception as e:
        logger.error(f"获取教室详情错误: {e}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500