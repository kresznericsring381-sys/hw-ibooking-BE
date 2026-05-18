# ================== 管理端接口层 ==================
"""
admin.py - 管理端相关的 API 接口

接口列表：
1. GET /api/admin/orders - 订单监控列表（多表联查）
2. POST /api/admin/orders/<id>/cancel - 强制取消订单
3. GET /api/admin/dashboard - 数据统计（可选）
"""

from flask import Blueprint, request, jsonify
from dao.order_dao import order_dao
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建蓝图
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/orders', methods=['GET'])
def get_all_orders():
    """
    订单监控列表（多表联查）
    
    用于后台监控，显示所有订单的完整信息
    
    查询参数：
    - status: 订单状态（可选）0=待签到, 1=使用中, 2=已完成, 3=违约, 4=取消
    - room_id: 教室 ID（可选）
    - page: 页码（可选，默认 1）
    - page_size: 每页条数（可选，默认 20）
    
    示例：
    GET /api/admin/orders
    GET /api/admin/orders?status=0&page=1&page_size=20
    GET /api/admin/orders?room_id=1
    
    响应：
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
            },
            ...
        ]
    }
    """
    try:
        # 获取查询参数
        status = request.args.get('status', type=int)
        room_id = request.args.get('room_id', type=int)
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 调用 DAO 获取订单
        orders = order_dao.get_all_orders_with_details(
            status=status,
            room_id=room_id,
            limit=page_size,
            offset=offset
        )
        
        # 获取总数（可选，为了计算总页数）
        total_sql = """
        SELECT COUNT(*) as cnt FROM orders o
        LEFT JOIN seat se ON o.seat_id = se.id
        WHERE 1=1
        """
        params = []
        if status is not None:
            total_sql += " AND o.status = %s"
            params.append(status)
        if room_id is not None:
            total_sql += " AND se.room_id = %s"
            params.append(room_id)
        
        from utils.db import db
        total_result = db.execute_query_one(total_sql, params)
        total = total_result['cnt'] if total_result else 0
        
        return jsonify({
            'success': True,
            'total': total,
            'page': page,
            'page_size': page_size,
            'orders': orders
        }), 200
    
    except Exception as e:
        logger.error(f"获取订单列表错误: {e}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@admin_bp.route('/orders/<int:order_id>/cancel', methods=['POST'])
def force_cancel_order(order_id):
    """
    【任务四】强制取消订单
    
    管理端可以强制取消任意订单
    
    示例：
    POST /api/admin/orders/123/cancel
    
    响应：
    {
        "success": true,
        "message": "订单已取消"
    }
    """
    try:
        # 取消订单
        affected = order_dao.cancel_order(order_id)
        
        if affected > 0:
            logger.info(f"管理员强制取消订单: {order_id}")
            return jsonify({
                'success': True,
                'message': '订单已取消'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '订单不存在'
            }), 404
    
    except Exception as e:
        logger.error(f"取消订单错误: {e}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@admin_bp.route('/dashboard', methods=['GET'])
def get_dashboard():
    """
    【扩展】获取后台统计数据（可选功能）
    
    返回系统的实时统计信息
    
    响应：
    {
        "success": true,
        "data": {
            "total_orders": 1000,
            "pending_orders": 50,
            "in_use_orders": 30,
            "completed_orders": 850,
            "violated_orders": 70,
            "total_seats": 500,
            "occupied_seats": 150
        }
    }
    """
    try:
        from utils.db import db
        
        # 获取各种统计数据
        order_stats = db.execute_query_one("""
            SELECT 
                COUNT(*) as total_orders,
                SUM(CASE WHEN status=0 THEN 1 ELSE 0 END) as pending_orders,
                SUM(CASE WHEN status=1 THEN 1 ELSE 0 END) as in_use_orders,
                SUM(CASE WHEN status=2 THEN 1 ELSE 0 END) as completed_orders,
                SUM(CASE WHEN status=3 THEN 1 ELSE 0 END) as violated_orders
            FROM orders
        """)
        
        seat_stats = db.execute_query_one("""
            SELECT 
                COUNT(*) as total_seats,
                SUM(CASE WHEN status=0 THEN 1 ELSE 0 END) as occupied_seats
            FROM seat
        """)
        
        return jsonify({
            'success': True,
            'data': {
                'total_orders': order_stats['total_orders'] or 0,
                'pending_orders': order_stats['pending_orders'] or 0,
                'in_use_orders': order_stats['in_use_orders'] or 0,
                'completed_orders': order_stats['completed_orders'] or 0,
                'violated_orders': order_stats['violated_orders'] or 0,
                'total_seats': seat_stats['total_seats'] or 0,
                'occupied_seats': seat_stats['occupied_seats'] or 0
            }
        }), 200
    
    except Exception as e:
        logger.error(f"获取统计数据错误: {e}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500