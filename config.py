# ================== 配置文件 ==================
import os
from datetime import timedelta

class Config:
    """基础配置"""
    # Flask 配置
    FLASK_ENV = 'development'
    DEBUG = True
    
    # 数据库配置
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': '118snake',  # 改成你的 MySQL 密码
        'database': 'school',
        'charset': 'utf8mb4',
        'cursorclass': 'DictCursor'
    }
    
    # 业务配置
    SEAT_TIMEOUT_MINUTES = 30  # 未签到超时时间（分钟）
    MAX_APPOINTMENT_DAYS = 7    # 最多提前预约天数
    
    # 定时任务配置
    SCHEDULER_CONFIG = {
        'apscheduler.jobstores.default': {
            'type': 'memory'
        },
        'apscheduler.executors.default': {
            'type': 'threading',
            'max_workers': 20
        },
        'apscheduler.job_defaults.coalesce': True,
        'apscheduler.job_defaults.max_instances': 1,
        'apscheduler.timezone': 'Asia/Shanghai'
    }

    # JWT 配置
    JWT_SECRET_KEY = 'ibooking_2025_secret'
    JWT_EXPIRE_HOURS = 24
