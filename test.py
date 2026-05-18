from flask import Flask, request, jsonify
import pymysql
from datetime import timedelta

app = Flask(__name__)

# 数据库配置（改成你自己的密码）
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '118snake',  # 这里改你的MySQL密码
    'database': 'school',
    'charset': 'utf8mb4'
}

# 数据库连接
def get_conn():
    return pymysql.connect(**db_config)

# 关键！把 timedelta 转成字符串 hh:mm:ss
def format_timedelta(td):
    if isinstance(td, timedelta):
        total_seconds = int(td.total_seconds())
        h = total_seconds // 3600
        m = (total_seconds % 3600) // 60
        s = total_seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
    return td

# 统一处理房间数据的时间格式
def format_room_time(rooms):
    for room in rooms:
        room['open_time'] = format_timedelta(room['open_time'])
        room['close_time'] = format_timedelta(room['close_time'])
    return rooms

# ===================== 接口 =====================

# 1. 登录
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    student_id = data.get('student_id')
    password = data.get('password')

    conn = get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM student WHERE student_id=%s AND password=%s",
                   (student_id, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({"code": 200, "msg": "登录成功", "data": user})
    else:
        return jsonify({"code": 401, "msg": "学号或密码错误"}), 401

# 2. 获取所有教室（已修复时间格式！）
@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    conn = get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM room WHERE status=1")
    rooms = cursor.fetchall()
    conn.close()

    # 修复时间格式
    rooms = format_room_time(rooms)

    return jsonify({"code": 200, "data": rooms})

if __name__ == '__main__':
    app.run(debug=True, port=5000)