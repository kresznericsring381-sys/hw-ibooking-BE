from flask import Blueprint, request, jsonify
from dao.user_dao import UserDao
from utils.token import generate_token

user_bp = Blueprint('user', __name__, url_prefix='/api')

# 注册
@user_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    student_id = data.get('student_id')
    password = data.get('password')
    name = data.get('name')

    if not all([student_id, password, name]):
        return jsonify({"code": 400, "msg": "参数不全"})

    # 检查学号是否存在
    dao = UserDao()
    student = dao.find_student_by_id(student_id)
    if student:
        return jsonify({"code": 400, "msg": "学号已注册"})

    # 注册
    dao.add_student(student_id, name, password)
    return jsonify({"code": 200, "msg": "注册成功"})

# 登录（返回Token）
@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    student_id = data.get('student_id')
    password = data.get('password')

    dao = UserDao()
    student = dao.find_student_by_id(student_id)

    if not student or student['password'] != password:
        return jsonify({"code": 401, "msg": "学号或密码错误"})

    # 生成JWT
    token = generate_token(student_id)
    return jsonify({
        "code": 200,
        "msg": "登录成功",
        "data": {
            "token": token,
            "student_id": student_id,
            "name": student['name']
        }
    })