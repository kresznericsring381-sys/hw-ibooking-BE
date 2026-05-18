# ================== 定时任务管理 ==================
"""
scheduler.py - APScheduler 定时任务配置

主要任务：
1. 每分钟清理违约订单（开始时间 > 30分钟未签到 → 违约）
2. 每日定时报表统计
3. 其他业务定时任务
"""

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from utils.db import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局调度器
scheduler = BackgroundScheduler()


def cleanup_expired_orders():
    """
    【任务四】每分钟执行 - 清理违约订单
    
    逻辑：
    1. 查询所有 status=0 的订单
    2. 检查 start_time + 30分钟 是否已过
    3. 自动设置为 status=3（违约）
    """
    try:
        logger.info("=== 开始清理违约订单 ===")
        
        sql = """
        SELECT id, student_id, seat_id, start_time 
        FROM orders 
        WHERE status = 0 
        AND DATE_ADD(start_time, INTERVAL 30 MINUTE) <= NOW()
        """
        
        expired_orders = db.execute_query(sql)
        
        if expired_orders:
            for order in expired_orders:
                order_id = order['id']
                seat_id = order['seat_id']
                
                # 将订单标记为违约
                update_sql = "UPDATE orders SET status=3 WHERE id=%s"
                db.execute_update(update_sql, (order_id,))
                
                logger.info(f"订单 {order_id} 标记为违约")
        
        logger.info(f"清理完成，共处理 {len(expired_orders)} 条违约订单")
    
    except Exception as e:
        logger.error(f"清理违约订单失败: {e}")


def init_scheduler():
    """
    初始化定时任务调度器
    
    调用时机：在 app.py 的 Flask 应用启动时调用
    """
    # 清理违约订单：每分钟执行一次
    scheduler.add_job(
        cleanup_expired_orders,
        'interval',
        minutes=1,
        id='cleanup_orders',
        name='清理违约订单',
        replace_existing=True
    )
    
    # 可添加其他定时任务...
    # scheduler.add_job(
    #     other_task,
    #     'cron',
    #     hour=0, minute=0,  # 每天凌晨
    #     id='daily_report',
    #     name='日常报表'
    # )
    
    if not scheduler.running:
        scheduler.start()
        logger.info("定时任务调度器已启动")


def stop_scheduler():
    """停止调度器"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("定时任务调度器已停止")
