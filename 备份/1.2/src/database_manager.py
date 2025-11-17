"""
增强的数据库管理器
提供连接池、事务管理和数据安全保证
"""

import sqlite3
import threading
import time
import os
from queue import Queue, Empty
from contextlib import contextmanager
from typing import Optional, Any, List, Tuple
from datetime import datetime


class DatabaseConnectionPool:
    """数据库连接池"""
    
    def __init__(self, db_path: str, pool_size: int = 5, timeout: float = 30.0):
        """
        初始化连接池
        
        Args:
            db_path: 数据库文件路径
            pool_size: 连接池大小
            timeout: 连接超时时间（秒）
        """
        self.db_path = db_path
        self.pool_size = pool_size
        self.timeout = timeout
        self.pool = Queue(maxsize=pool_size)
        self.lock = threading.Lock()
        self._closed = False
        
        # 确保数据库目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 初始化连接池
        for _ in range(pool_size):
            conn = self._create_connection()
            if conn:
                self.pool.put(conn)
    
    def _create_connection(self) -> Optional[sqlite3.Connection]:
        """创建数据库连接"""
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=self.timeout,
                check_same_thread=False,
                isolation_level='DEFERRED'
            )
            # 启用外键约束
            conn.execute("PRAGMA foreign_keys = ON")
            # 设置WAL模式（提高并发性能）
            conn.execute("PRAGMA journal_mode = WAL")
            # 设置同步模式
            conn.execute("PRAGMA synchronous = NORMAL")
            return conn
        except sqlite3.Error as e:
            print(f"创建数据库连接失败: {e}")
            return None
    
    @contextmanager
    def get_connection(self, timeout: Optional[float] = None):
        """
        获取数据库连接（上下文管理器）
        
        Args:
            timeout: 获取连接的超时时间
            
        Yields:
            sqlite3.Connection: 数据库连接
        """
        if self._closed:
            raise RuntimeError("连接池已关闭")
        
        conn = None
        wait_timeout = timeout or self.timeout
        
        try:
            conn = self.pool.get(timeout=wait_timeout)
            
            # 检查连接是否有效
            if not self._is_connection_valid(conn):
                conn.close()
                conn = self._create_connection()
            
            if conn is None:
                raise RuntimeError("无法创建有效的数据库连接")
            
            yield conn
            
        except Empty:
            raise TimeoutError(f"获取数据库连接超时（{wait_timeout}秒）")
        
        finally:
            if conn and not self._closed:
                try:
                    self.pool.put(conn, block=False)
                except:
                    # 如果放回失败，关闭连接
                    conn.close()
    
    def _is_connection_valid(self, conn: sqlite3.Connection) -> bool:
        """检查连接是否有效"""
        try:
            conn.execute("SELECT 1")
            return True
        except sqlite3.Error:
            return False
    
    def close_all(self):
        """关闭所有连接"""
        with self.lock:
            self._closed = True
            
            while not self.pool.empty():
                try:
                    conn = self.pool.get_nowait()
                    conn.close()
                except Empty:
                    break
                except Exception as e:
                    print(f"关闭连接时出错: {e}")
    
    def __del__(self):
        """析构函数"""
        self.close_all()


class SafeDatabaseManager:
    """安全的数据库管理器"""
    
    def __init__(self, db_path: str, pool_size: int = 5):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
            pool_size: 连接池大小
        """
        self.db_path = db_path
        self.pool = DatabaseConnectionPool(db_path, pool_size)
        self.lock = threading.Lock()
    
    def execute_with_retry(self, sql: str, params: Tuple = (), 
                          max_retries: int = 3) -> Optional[sqlite3.Cursor]:
        """
        执行SQL语句（带重试）
        
        Args:
            sql: SQL语句
            params: 参数
            max_retries: 最大重试次数
            
        Returns:
            Optional[Cursor]: 游标对象
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                with self.pool.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(sql, params)
                    conn.commit()
                    return cursor
            
            except sqlite3.OperationalError as e:
                last_error = e
                if "locked" in str(e).lower():
                    # 数据库锁定，等待后重试
                    wait_time = 0.1 * (2 ** attempt)  # 指数退避
                    time.sleep(wait_time)
                    continue
                else:
                    raise
            
            except sqlite3.IntegrityError as e:
                # 完整性约束错误，不重试
                print(f"数据完整性错误: {e}")
                raise
            
            except Exception as e:
                last_error = e
                print(f"数据库操作失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.5)
        
        if last_error:
            raise last_error
        
        return None
    
    def execute_many_with_retry(self, sql: str, params_list: List[Tuple],
                               max_retries: int = 3) -> bool:
        """
        批量执行SQL语句（带重试）
        
        Args:
            sql: SQL语句
            params_list: 参数列表
            max_retries: 最大重试次数
            
        Returns:
            bool: 是否成功
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                with self.pool.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.executemany(sql, params_list)
                    conn.commit()
                    return True
            
            except sqlite3.OperationalError as e:
                last_error = e
                if "locked" in str(e).lower():
                    wait_time = 0.1 * (2 ** attempt)
                    time.sleep(wait_time)
                    continue
                else:
                    raise
            
            except Exception as e:
                last_error = e
                print(f"批量操作失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.5)
        
        if last_error:
            raise last_error
        
        return False
    
    def query_with_retry(self, sql: str, params: Tuple = (),
                        max_retries: int = 3) -> List[Tuple]:
        """
        查询数据（带重试）
        
        Args:
            sql: SQL查询语句
            params: 参数
            max_retries: 最大重试次数
            
        Returns:
            List[Tuple]: 查询结果
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                with self.pool.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(sql, params)
                    results = cursor.fetchall()
                    return results
            
            except sqlite3.OperationalError as e:
                last_error = e
                if "locked" in str(e).lower():
                    wait_time = 0.1 * (2 ** attempt)
                    time.sleep(wait_time)
                    continue
                else:
                    raise
            
            except Exception as e:
                last_error = e
                print(f"查询失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.5)
        
        if last_error:
            raise last_error
        
        return []
    
    @contextmanager
    def transaction(self):
        """
        事务上下文管理器
        
        使用示例:
            with db_manager.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT ...")
                cursor.execute("UPDATE ...")
                # 自动提交或回滚
        """
        with self.pool.get_connection() as conn:
            try:
                conn.execute("BEGIN TRANSACTION")
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                print(f"事务回滚: {e}")
                raise
    
    def backup_database(self, backup_path: Optional[str] = None) -> bool:
        """
        备份数据库
        
        Args:
            backup_path: 备份文件路径（None则自动生成）
            
        Returns:
            bool: 是否成功
        """
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(os.path.dirname(self.db_path), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = os.path.join(backup_dir, f"backup_{timestamp}.db")
        
        try:
            with self.pool.get_connection() as source_conn:
                backup_conn = sqlite3.connect(backup_path)
                source_conn.backup(backup_conn)
                backup_conn.close()
                print(f"数据库备份成功: {backup_path}")
                return True
        except Exception as e:
            print(f"数据库备份失败: {e}")
            return False
    
    def vacuum(self) -> bool:
        """
        清理数据库（回收空间）
        
        Returns:
            bool: 是否成功
        """
        try:
            with self.pool.get_connection() as conn:
                conn.execute("VACUUM")
                print("数据库清理完成")
                return True
        except Exception as e:
            print(f"数据库清理失败: {e}")
            return False
    
    def get_table_info(self, table_name: str) -> List[Tuple]:
        """
        获取表结构信息
        
        Args:
            table_name: 表名
            
        Returns:
            List[Tuple]: 表结构信息
        """
        sql = f"PRAGMA table_info({table_name})"
        return self.query_with_retry(sql)
    
    def close(self):
        """关闭数据库管理器"""
        self.pool.close_all()


# 全局数据库管理器实例
_db_manager: Optional[SafeDatabaseManager] = None


def get_db_manager(db_path: str = None) -> SafeDatabaseManager:
    """
    获取数据库管理器实例
    
    Args:
        db_path: 数据库文件路径
        
    Returns:
        SafeDatabaseManager: 数据库管理器
    """
    global _db_manager
    
    if _db_manager is None:
        if db_path is None:
            db_path = os.path.join("logs", "douyin_stats.db")
        _db_manager = SafeDatabaseManager(db_path)
    
    return _db_manager

