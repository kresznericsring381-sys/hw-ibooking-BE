from flask import Flask
from api.user_api import user_bp
from api.room_api import room_bp
from api.order_api import order_bp

app = Flask(__name__)

# 注册蓝图（任务三全部接口）
app.register_blueprint(user_bp)
app.register_blueprint(room_bp)
app.register_blueprint(order_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)