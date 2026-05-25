from functools import wraps
from flask import request, jsonify
from utils.token import verify_token


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.headers.get('token')
        if not token:
            return jsonify({'code': 401, 'msg': '请先登录'})

        student_id = verify_token(token)
        if not student_id:
            return jsonify({'code': 401, 'msg': '登录已过期'})

        # 把学生ID传入接口
        return func(student_id, *args, **kwargs)

    return wrapper