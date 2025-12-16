"""
视频任务数据库模块
记录已扫描回复过的视频，避免重复执行任务

表结构：
- video_id: 视频唯一标识
- product_name: 产品名称
- keyword: 使用的搜索关键词
- replies_count: 回复数量
- scanned_at: 扫描时间
"""

import os
import sqlite3
from datetime import datetime
from typing import Optional, List, Tuple

# 数据库路径
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
DB_PATH = os.path.join(DB_DIR, 'video_tasks.db')


def _ensure_db_exists():
    """确保数据库和表存在"""
    os.makedirs(DB_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建视频任务记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scanned_videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT NOT NULL,
            product_name TEXT NOT NULL,
            keyword TEXT,
            replies_count INTEGER DEFAULT 0,
            scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(video_id, product_name)
        )
    ''')
    
    # 创建索引加速查询
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_video_product 
        ON scanned_videos(video_id, product_name)
    ''')
    
    conn.commit()
    conn.close()


def is_video_scanned(video_id: str, product_name: str) -> bool:
    """
    检查视频是否已被扫描过
    
    Args:
        video_id: 视频ID
        product_name: 产品名称
        
    Returns:
        bool: True=已扫描过，False=未扫描
    """
    _ensure_db_exists()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 1 FROM scanned_videos 
        WHERE video_id = ? AND product_name = ?
        LIMIT 1
    ''', (video_id, product_name))
    
    result = cursor.fetchone()
    conn.close()
    
    return result is not None


def record_scanned_video(video_id: str, product_name: str, 
                         keyword: str = "", replies_count: int = 0) -> bool:
    """
    记录已扫描的视频
    
    Args:
        video_id: 视频ID
        product_name: 产品名称
        keyword: 使用的搜索关键词
        replies_count: 本次回复数量
        
    Returns:
        bool: 记录成功返回True
    """
    _ensure_db_exists()
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO scanned_videos 
            (video_id, product_name, keyword, replies_count, scanned_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (video_id, product_name, keyword, replies_count, 
              datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[video_db] 记录失败: {e}")
        return False


def get_scanned_count(product_name: str = None) -> int:
    """
    获取已扫描视频数量
    
    Args:
        product_name: 产品名称，None则统计所有
        
    Returns:
        int: 已扫描视频数量
    """
    _ensure_db_exists()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if product_name:
        cursor.execute('''
            SELECT COUNT(*) FROM scanned_videos WHERE product_name = ?
        ''', (product_name,))
    else:
        cursor.execute('SELECT COUNT(*) FROM scanned_videos')
    
    count = cursor.fetchone()[0]
    conn.close()
    
    return count


def get_recent_scanned(limit: int = 10, product_name: str = None) -> List[Tuple]:
    """
    获取最近扫描的视频列表
    
    Args:
        limit: 返回数量
        product_name: 产品名称筛选
        
    Returns:
        List[Tuple]: (video_id, product_name, keyword, replies_count, scanned_at)
    """
    _ensure_db_exists()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if product_name:
        cursor.execute('''
            SELECT video_id, product_name, keyword, replies_count, scanned_at
            FROM scanned_videos 
            WHERE product_name = ?
            ORDER BY scanned_at DESC
            LIMIT ?
        ''', (product_name, limit))
    else:
        cursor.execute('''
            SELECT video_id, product_name, keyword, replies_count, scanned_at
            FROM scanned_videos 
            ORDER BY scanned_at DESC
            LIMIT ?
        ''', (limit,))
    
    results = cursor.fetchall()
    conn.close()
    
    return results


def clear_old_records(days: int = 30) -> int:
    """
    清理超过指定天数的旧记录
    
    Args:
        days: 保留天数
        
    Returns:
        int: 删除的记录数
    """
    _ensure_db_exists()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        DELETE FROM scanned_videos 
        WHERE scanned_at < datetime('now', '-' || ? || ' days')
    ''', (days,))
    
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    return deleted


# 初始化数据库
_ensure_db_exists()
