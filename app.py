# ================== Flask 应用入口 ==================
"""
app.py - 分层架构后的主程序入口

架构：
├── config.py           # 配置
├── api/                # 接口层（路由）
├── service/            # 业务逻辑层
├── dao/                # 数据访问层
└── utils/              # 工具（数据库、定时任务）

启动方式：
python app.py
"""

from flask import Flask, request, jsonify
import pymysql
from config import Config
from utils.scheduler import init_scheduler, stop_scheduler
from api.seat import seat_bp
from api.order import order_bp
from api.admin import admin_bp
from api.room import room_bp
from utils.db import db
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 Flask 应用
app = Flask(__name__)
app.config.from_object(Config)

# ================== 注册蓝图 ==================
app.register_blueprint(seat_bp)
app.register_blueprint(order_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(room_bp)


# ================== 用户认证接口 ==================

@app.route('/api/login', methods=['POST'])
def login():
    """
    学生登录接口
    
    请求格式：
    {
        "student_id": "2024001",
        "password": "password123"
    }
    
    响应：
    {
        "success": true,
        "student_id": "2024001",
        "name": "张三",
        "message": "登录成功"
    }
    """
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        password = data.get('password')
        
        if not student_id or not password:
            return jsonify({
                'success': False,
                'message': '学号和密码不能为空'
            }), 400
        
        sql = "SELECT student_id, name FROM student WHERE student_id=%s AND password=%s"
        user = db.execute_query_one(sql, (student_id, password))
        
        if user:
            logger.info(f"学生 {student_id} 登录成功")
            return jsonify({
                'success': True,
                'student_id': user['student_id'],
                'name': user['name'],
                'message': '登录成功'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '学号或密码错误'
            }), 401
    
    except Exception as e:
        logger.error(f"登录错误: {e}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@app.route('/api/register', methods=['POST'])
def register():
    """
    学生注册接口
    
    请求格式：
    {
        "student_id": "2024001",
        "name": "张三",
        "password": "password123"
    }
    
    响应：
    {
        "success": true,
        "message": "注册成功"
    }
    """
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        name = data.get('name')
        password = data.get('password')
        
        if not all([student_id, name, password]):
            return jsonify({
                'success': False,
                'message': '参数不完整'
            }), 400
        
        # 检查是否已注册
        check_sql = "SELECT id FROM student WHERE student_id=%s"
        existing = db.execute_query_one(check_sql, (student_id,))
        
        if existing:
            return jsonify({
                'success': False,
                'message': '学号已存在'
            }), 400
        
        # 插入新学生
        insert_sql = "INSERT INTO student (student_id, name, password) VALUES (%s, %s, %s)"
        db.execute_update(insert_sql, (student_id, name, password))
        
        logger.info(f"学生注册成功: {student_id}")
        
        return jsonify({
            'success': True,
            'message': '注册成功'
        }), 201
    
    except Exception as e:
        logger.error(f"注册错误: {e}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    
    响应：
    {
        "status": "healthy"
    }
    """
    return jsonify({'status': 'healthy'}), 200


# ================== 错误处理 ==================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': '请求的资源不存在'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"服务器内部错误: {error}")
    return jsonify({
        'success': False,
        'message': '服务器内部错误'
    }), 500


# ================== 应用启动 ==================

if __name__ == '__main__':
    try:
        logger.info("=" * 50)
        logger.info("🚀 房间预约系统后端启动")
        logger.info("=" * 50)
        
        # 启动定时任务
        init_scheduler()
        
        # 启动 Flask 应用
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False  # 避免定时任务重复启动
        )
    
    except KeyboardInterrupt:
        logger.info("应用被中断")
        stop_scheduler()
    
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        stop_scheduler()