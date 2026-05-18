# ================== 座位接口层 ==================
"""
seat.py - 座位相关的 API 接口

接口列表：
1. POST /api/admin/seat/init - 批量初始化座位
2. GET /api/rooms/<id>/seats - 获取座位状态
"""

from flask import Blueprint, request, jsonify
from service.seat_service import seat_service
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建蓝图
seat_bp = Blueprint('seat', __name__, url_prefix='/api')


@seat_bp.route('/admin/seat/init', methods=['POST'])
def init_room_seats():
    """
    【任务二】批量初始化座位
    
    请求格式：
    {
        "room_id": 1,
        "rows": 10,
        "cols": 10
    }
    
    响应：
    {
        "success": true,
        "message": "座位初始化成功",
        "count": 100,
        "room_id": 1,
        "grid": {"rows": 10, "cols": 10}
    }
    """
    try:
        data = request.get_json()
        room_id = data.get('room_id')
        rows = data.get('rows')
        cols = data.get('cols')
        
        # 参数验证
        if not room_id or not rows or not cols:
            return jsonify({
                'success': False,
                'message': '参数不完整：需要 room_id, rows, cols'
            }), 400
        
        # 调用业务服务
        result = seat_service.init_room_seats(room_id, rows, cols)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"初始化座位错误: {e}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@seat_bp.route('/rooms/<int:room_id>/seats', methods=['GET'])
def get_room_seats(room_id):
    """
    【任务二】获取教室座位实时状态
    
    查询参数：
    - start_time: 开始时间 (ISO 格式，如 2024-05-06T09:00:00)
    - end_time: 结束时间 (ISO 格式)
    
    示例：
    GET /api/rooms/1/seats?start_time=2024-05-06T09:00:00&end_time=2024-05-06T11:00:00
    
    响应：
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
                "is_occupied": 0,  # 0=绿色, 1=红色
                "student_id": null,
                "order_id": null
            },
            ...
        ]
    }
    """
    try:
        # 获取查询参数
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        
        if not start_time or not end_time:
            return jsonify({
                'success': False,
                'message': '缺少查询参数: start_time, end_time'
            }), 400
        
        # 调用业务服务
        result = seat_service.get_room_seats_status(room_id, start_time, end_time)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"获取座位状态错误: {e}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500
