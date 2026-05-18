# ================== 数据库连接与事务管理 ==================
"""
db.py - 统一管理数据库连接、事务、行级锁

核心功能：
1. 数据库连接池
2. 事务管理（BEGIN、COMMIT、ROLLBACK）
3. 行级排他锁（FOR UPDATE）防超卖
"""

import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Database:
    """数据库管理类"""
    
    def __init__(self):
        self.db_config = Config.DB_CONFIG
        self.db_config['cursorclass'] = DictCursor
    
    def get_connection(self):
        """获取数据库连接"""
        try:
            conn = pymysql.connect(**self.db_config)
            return conn
        except pymysql.Error as e:
            logger.error(f"数据库连接失败: {e}")
            raise
    
    @contextmanager
    def get_cursor(self, conn=None):
        """获取数据库游标（上下文管理器）"""
        if conn is None:
            conn = self.get_connection()
            close_conn = True
        else:
            close_conn = False
        
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()
            if close_conn:
                conn.close()
    
    @contextmanager
    def transaction(self):
        """
        事务管理（上下文管理器）
        
        用法示例：
        with db.transaction() as (conn, cursor):
            cursor.execute(...)
            cursor.execute(...)
        # 自动 COMMIT，异常自动 ROLLBACK
        """
        conn = self.get_connection()
        try:
            conn.begin()  # 显式开启事务
            cursor = conn.cursor()
            yield (conn, cursor)
            cursor.close()
            conn.commit()
            logger.info("事务提交成功")
        except Exception as e:
            conn.rollback()
            logger.error(f"事务回滚: {e}")
            raise
        finally:
            conn.close()
    
    def execute_query(self, sql, params=None):
        """
        执行查询语句
        
        返回：查询结果列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, params)
            result = cursor.fetchall()
            return result
        finally:
            cursor.close()
            conn.close()
    
    def execute_query_one(self, sql, params=None):
        """
        执行查询语句（返回单条记录）
        
        返回：单条记录或 None
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, params)
            result = cursor.fetchone()
            return result
        finally:
            cursor.close()
            conn.close()
    
    def execute_update(self, sql, params=None):
        """
        执行更新/删除/插入语句（非事务）
        
        返回：受影响行数
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, params)
            conn.commit()
            affected_rows = cursor.rowcount
            return affected_rows
        except Exception as e:
            conn.rollback()
            logger.error(f"更新失败: {e}")
            raise
        finally:
            cursor.close()
            conn.close()


# 全局数据库实例
db = Database()


# ================== 常用查询辅助函数 ==================

def execute_with_lock(sql_select, sql_update, select_params=None, update_params=None):
    """
    【关键】带行级排他锁的事务执行
    
    场景：预约前先锁定座位，防止超卖
    
    示例：
    def make_order(seat_id):
        def lock_query():
            return "SELECT * FROM seat WHERE id=%s FOR UPDATE"
        def update_query():
            return "INSERT INTO orders ..."
        execute_with_lock(lock_query, update_query, (seat_id,), (...))
    """
    try:
        with db.transaction() as (conn, cursor):
            # 1. 执行 SELECT ... FOR UPDATE （锁定座位）
            cursor.execute(sql_select, select_params)
            locked_record = cursor.fetchone()
            
            if not locked_record:
                raise ValueError("座位不存在")
            
            # 2. 执行更新操作
            cursor.execute(sql_update, update_params)
            
            # 事务自动提交
            return {'success': True, 'data': locked_record}
    
    except Exception as e:
        logger.error(f"锁定操作失败: {e}")
        raise


def batch_insert(table, columns, data_list):
    """
    【关键】批量插入优化
    
    场景：初始化座位网格时批量生成
    
    参数：
    - table: 表名
    - columns: 列名列表 ['id', 'room_id', 'x', 'y']
    - data_list: 数据列表 [(...), (...)]
    
    返回：受影响行数
    """
    if not data_list:
        return 0
    
    placeholders = ','.join(['%s'] * len(columns))
    sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
    
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.executemany(sql, data_list)
        conn.commit()
        affected_rows = cursor.rowcount
        logger.info(f"批量插入 {table}: {affected_rows} 行")
        return affected_rows
    except Exception as e:
        conn.rollback()
        logger.error(f"批量插入失败: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
