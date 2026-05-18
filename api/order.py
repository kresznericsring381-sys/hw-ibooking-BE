# ================== 订单接口层 ==================
"""
order.py - 订单相关的 API 接口

接口列表：
1. POST /api/orders - 创建订单（预约）
2. GET /api/orders - 获取用户订单列表
3. POST /api/orders/<id>/checkin - 签到
4. POST /api/orders/<id>/complete - 完成
"""

from flask import Blueprint, request, jsonify
from service.order_service import order_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建蓝图
order_bp = Blueprint('order', __name__, url_prefix='/api')


@order_bp.route('/orders', methods=['POST'])
def create_order():
    """
    【任务三】创建订单（预约座位）
    
    请求格式：
    {
        "student_id": "2024001",
        "seat_id": 5,
        "room_id": 1,
        "start_time": "2024-05-06T09:00:00",
        "end_time": "2024-05-06T11:00:00"
    }
    
    响应：
    {
        "success": true,
        "order_id": 123,
        "message": "预约成功"
    }
    
    故障响应示例：
    {
        "success": false,
        "message": "您在该时间段已有其他预约"
    }
    """
    try:
        data = request.get_json()
        
        # 参数验证
        required_fields = ['student_id', 'seat_id', 'room_id', 'start_time', 'end_time']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'缺少必要参数: {field}'
                }), 400
        
        # 调用业务服务
        result = order_service.make_appointment(
            student_id=data['student_id'],
            seat_id=data['seat_id'],
            room_id=data['room_id'],
            start_time=data['start_time'],
            end_time=data['end_time']
        )
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"创建订单错误: {e}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@order_bp.route('/orders', methods=['GET'])
def get_orders():
    """
    【任务三】获取用户订单列表
    
    查询参数：
    - student_id: 学生学号（必须）
    - status: 订单状态（可选）0=待签到, 1=使用中, 2=已完成, 3=违约, 4=取消
    
    示例：
    GET /api/orders?student_id=2024001
    GET /api/orders?student_id=2024001&status=0
    
    响应：
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
            },
            ...
        ]
    }
    """
    try:
        student_id = request.args.get('student_id')
        status = request.args.get('status', type=int)
        
        if not student_id:
            return jsonify({
                'success': False,
                'message': '缺少参数: student_id'
            }), 400
        
        # 调用业务服务
        result = order_service.get_student_orders(student_id, status)
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"获取订单列表错误: {e}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@order_bp.route('/orders/<int:order_id>/checkin', methods=['POST'])
def checkin(order_id):
    """
    【任务三】签到订单
    
    状态：0（待签到）→ 1（使用中）
    
    示例：
    POST /api/orders/123/checkin
    
    响应：
    {
        "success": true,
        "message": "签到成功"
    }
    """
    try:
        result = order_service.check_in(order_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"签到错误: {e}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@order_bp.route('/orders/<int:order_id>/complete', methods=['POST'])
def complete(order_id):
    """
    【任务三】完成订单
    
    状态：1（使用中）→ 2（已完成）
    
    示例：
    POST /api/orders/123/complete
    
    响应：
    {
        "success": true,
        "message": "完成成功"
    }
    """
    try:
        result = order_service.complete(order_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"完成订单错误: {e}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500
