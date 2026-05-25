from flask import Blueprint, request, jsonify
from utils.decorators import login_required
from dao.order_dao import OrderDao
from dao.room_dao import RoomDao
from datetime import datetime

order_bp = Blueprint('order', __name__, url_prefix='/api')

# ====================== 任务三：预约时间校验 ======================
@order_bp.route('/orders', methods=['POST'])
@login_required
def create_order(student_id):
    data = request.get_json()
    seat_id = data.get('seat_id')
    start_time = data.get('start_time')
    end_time = data.get('end_time')

    # 1. 时间不能早于当前时间
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if start_time < now:
        return jsonify({"code":400, "msg":"预约时间不能早于当前时间"})

    # 2. 检查是否在教室开放时间内
    room_dao = RoomDao()
    seat = room_dao.get_seat_by_id(seat_id)
    room = room_dao.get_room_by_id(seat['room_id'])
    open_time = room['open_time']
    close_time = room['close_time']
    if not (open_time <= start_time[-8:] and end_time[-8:] <= close_time):
        return jsonify({"code":400, "msg":"不在教室开放时间内"})

    # 3. 座位冲突校验（你原有代码）
    order_dao = OrderDao()
    conflict = order_dao.check_conflict(seat_id, start_time, end_time)
    if conflict:
        return jsonify({"code":400, "msg":"该时间段已被预约"})

    # 4. 创建订单
    order_dao.create_order(student_id, seat_id, start_time, end_time)
    return jsonify({"code":200, "msg":"预约成功"})

# ====================== 任务三：签到时间校验 ======================
@order_bp.route('/orders/<int:id>/checkin', methods=['POST'])
@login_required
def checkin(student_id, id):
    order_dao = OrderDao()
    order = order_dao.get_order_by_id(id)

    if not order or order['student_id'] != student_id:
        return jsonify({"code":403, "msg":"无权限"})

    start_time = order['start_time']
    now = datetime.now()
    start = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")

    # 只能在开始前后30分钟内签到
    delta = abs((now - start).total_seconds())
    if delta > 1800:
        return jsonify({"code":400, "msg":"只能在预约开始前后30分钟内签到"})

    order_dao.update_status(id, 1)
    return jsonify({"code":200, "msg":"签到成功"})

# 结束订单
@order_bp.route('/orders/<int:id>/complete', methods=['POST'])
@login_required
def complete(student_id, id):
    order_dao = OrderDao()
    order_dao.update_status(id, 2)
    return jsonify({"code":200, "msg":"已完成"})

# 我的订单
@order_bp.route('/orders', methods=['GET'])
@login_required
def my_orders(student_id):
    order_dao = OrderDao()
    orders = order_dao.get_orders_by_student(student_id)
    return jsonify({"code":200, "data": orders})