from flask import Blueprint, request, jsonify
from dao.room_dao import RoomDao

room_bp = Blueprint('room', __name__, url_prefix='/api')

# 学生端：查看可用教室列表
@room_bp.route('/rooms', methods=['GET'])
def room_list():
    dao = RoomDao()
    rooms = dao.get_all_rooms()
    return jsonify({"code":200, "data": rooms})

# 管理端：新增教室
@room_bp.route('/admin/room', methods=['POST'])
def admin_add_room():
    data = request.get_json()
    name = data.get('name')
    open_time = data.get('open_time')
    close_time = data.get('close_time')
    status = data.get('status', 1)
    dao = RoomDao()
    dao.add_room(name, open_time, close_time, status)
    return jsonify({"code":200, "msg":"添加成功"})

# 管理端：修改教室
@room_bp.route('/admin/room/<int:id>', methods=['PUT'])
def admin_update_room(id):
    data = request.get_json()
    dao = RoomDao()
    dao.update_room(id, data)
    return jsonify({"code":200, "msg":"修改成功"})

# 管理端：删除教室
@room_bp.route('/admin/room/<int:id>', methods=['DELETE'])
def admin_delete_room(id):
    dao = RoomDao()
    dao.delete_room(id)
    return jsonify({"code":200, "msg":"删除成功"})