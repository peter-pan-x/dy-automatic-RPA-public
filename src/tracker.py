"""
数据持久化统计器 - 使用SQLite存储统计数据和运行状态
提供完整的统计功能和数据恢复能力
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import threading

class InteractionTracker:
    """交互统计器 - 支持SQLite数据持久化"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            # 默认存储在logs目录
            db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, 'douyin_stats.db')

        self.db_path = db_path
        self.lock = threading.Lock()

        # 内存中的统计数据
        self._stats = {
            'sessions_completed': 0,
            'videos_watched': 0,
            'likes_given': 0,
            'comments_posted': 0,
            'favorites_made': 0,
            'follows_added': 0,
            'searches_performed': 0,
            'errors_encountered': 0,
            'start_time': datetime.now(),
            'last_activity': datetime.now(),
            'current_session_start': datetime.now(),
            'current_session_type': None
        }

        # 初始化数据库
        self._init_database()
        # 加载已有数据
        self._load_stats()

    def _init_database(self):
        """初始化SQLite数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 创建统计表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT UNIQUE,
                    sessions_completed INTEGER DEFAULT 0,
                    videos_watched INTEGER DEFAULT 0,
                    likes_given INTEGER DEFAULT 0,
                    comments_posted INTEGER DEFAULT 0,
                    favorites_made INTEGER DEFAULT 0,
                    follows_added INTEGER DEFAULT 0,
                    searches_performed INTEGER DEFAULT 0,
                    errors_encountered INTEGER DEFAULT 0,
                    runtime_minutes INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 创建详细记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS interaction_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_type TEXT,
                    interaction_type TEXT,
                    content TEXT,
                    success BOOLEAN,
                    error_message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 创建运行状态表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS runtime_state (
                    key TEXT UNIQUE,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 创建会话记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_type TEXT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    videos_watched INTEGER DEFAULT 0,
                    interactions_count INTEGER DEFAULT 0,
                    success BOOLEAN,
                    notes TEXT
                )
            ''')

            conn.commit()

    def _load_stats(self):
        """从数据库加载统计数据"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    # 加载今日统计
                    today = datetime.now().strftime('%Y-%m-%d')
                    cursor.execute('SELECT * FROM daily_stats WHERE date = ?', (today,))
                    today_stats = cursor.fetchone()

                    if today_stats:
                        # 解析数据库数据
                        columns = [desc[0] for desc in cursor.description]
                        db_data = dict(zip(columns, today_stats))

                        # 更新内存统计
                        self._stats.update({
                            'sessions_completed': db_data.get('sessions_completed', 0),
                            'videos_watched': db_data.get('videos_watched', 0),
                            'likes_given': db_data.get('likes_given', 0),
                            'comments_posted': db_data.get('comments_posted', 0),
                            'favorites_made': db_data.get('favorites_made', 0),
                            'follows_added': db_data.get('follows_added', 0),
                            'searches_performed': db_data.get('searches_performed', 0),
                            'errors_encountered': db_data.get('errors_encountered', 0),
                        })

                    # 加载运行状态
                    cursor.execute('SELECT key, value FROM runtime_state')
                    runtime_data = cursor.fetchall()

                    for key, value in runtime_data:
                        if key == 'start_time':
                            self._stats['start_time'] = datetime.fromisoformat(value)
                        elif key == 'last_activity':
                            self._stats['last_activity'] = datetime.fromisoformat(value)
                        elif key == 'current_session_start':
                            self._stats['current_session_start'] = datetime.fromisoformat(value)
                        elif key == 'current_session_type':
                            self._stats['current_session_type'] = value

                    print(f"📊 已加载统计数据: {self.get_total_interactions()} 个交互")

            except Exception as e:
                print(f"⚠️ 加载数据失败: {e}")

    def _save_runtime_state(self):
        """保存运行状态到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 更新或插入运行状态
                runtime_data = [
                    ('start_time', self._stats['start_time'].isoformat()),
                    ('last_activity', self._stats['last_activity'].isoformat()),
                    ('current_session_start', self._stats['current_session_start'].isoformat()),
                    ('current_session_type', self._stats['current_session_type'] or ''),
                ]

                for key, value in runtime_data:
                    cursor.execute('''
                        INSERT OR REPLACE INTO runtime_state (key, value, updated_at)
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                    ''', (key, value))

                conn.commit()

        except Exception as e:
            print(f"⚠️ 保存运行状态失败: {e}")

    def _update_daily_stats(self):
        """更新每日统计数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                today = datetime.now().strftime('%Y-%m-%d')
                runtime_minutes = int((datetime.now() - self._stats['start_time']).total_seconds() / 60)

                cursor.execute('''
                    INSERT OR REPLACE INTO daily_stats
                    (date, sessions_completed, videos_watched, likes_given, comments_posted,
                     favorites_made, follows_added, searches_performed, errors_encountered,
                     runtime_minutes, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    today,
                    self._stats['sessions_completed'],
                    self._stats['videos_watched'],
                    self._stats['likes_given'],
                    self._stats['comments_posted'],
                    self._stats['favorites_made'],
                    self._stats['follows_added'],
                    self._stats['searches_performed'],
                    self._stats['errors_encountered'],
                    runtime_minutes
                ))

                conn.commit()

        except Exception as e:
            print(f"⚠️ 更新每日统计失败: {e}")

    def log_interaction(self, interaction_type: str, success: bool = True,
                       content: str = None, error_message: str = None,
                       session_type: str = None):
        """记录交互到数据库"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    cursor.execute('''
                        INSERT INTO interaction_log
                        (session_type, interaction_type, content, success, error_message)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (session_type or self._stats['current_session_type'],
                          interaction_type, content, success, error_message))

                    conn.commit()

                # 更新内存统计
                self._stats['last_activity'] = datetime.now()

                if success:
                    if interaction_type == 'watch':
                        self._stats['videos_watched'] += 1
                    elif interaction_type == 'like':
                        self._stats['likes_given'] += 1
                    elif interaction_type == 'comment':
                        self._stats['comments_posted'] += 1
                    elif interaction_type == 'favorite':
                        self._stats['favorites_made'] += 1
                    elif interaction_type == 'follow':
                        self._stats['follows_added'] += 1
                    elif interaction_type == 'search':
                        self._stats['searches_performed'] += 1
                else:
                    self._stats['errors_encountered'] += 1

                # 定期保存数据
                if self._stats['videos_watched'] % 10 == 0:  # 每观看10个视频保存一次
                    self._update_daily_stats()
                    self._save_runtime_state()

            except Exception as e:
                print(f"⚠️ 记录交互失败: {e}")

    def start_session(self, session_type: str):
        """开始新会话"""
        with self.lock:
            self._stats['current_session_type'] = session_type
            self._stats['current_session_start'] = datetime.now()
            print(f"🚀 开始会话: {session_type}")

    def complete_session(self, videos_watched: int = 0, interactions_count: int = 0,
                        success: bool = True, notes: str = None):
        """完成会话"""
        with self.lock:
            try:
                session_end = datetime.now()
                session_duration = session_end - self._stats['current_session_start']

                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    cursor.execute('''
                        INSERT INTO sessions
                        (session_type, start_time, end_time, videos_watched,
                         interactions_count, success, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        self._stats['current_session_type'],
                        self._stats['current_session_start'],
                        session_end,
                        videos_watched,
                        interactions_count,
                        success,
                        notes
                    ))

                    conn.commit()

                self._stats['sessions_completed'] += 1

                print(f"✅ 会话完成: {self._stats['current_session_type']} "
                      f"({session_duration.total_seconds():.1f}秒, "
                      f"{videos_watched}个视频)")

                # 更新数据库
                self._update_daily_stats()
                self._save_runtime_state()

            except Exception as e:
                print(f"⚠️ 完成会话记录失败: {e}")

    def get_total_interactions(self) -> int:
        """获取总交互数"""
        return (self._stats['likes_given'] + self._stats['comments_posted'] +
                self._stats['favorites_made'] + self._stats['follows_added'])

    def get_runtime_info(self) -> Dict[str, Any]:
        """获取运行时间信息"""
        runtime = datetime.now() - self._stats['start_time']
        current_session = datetime.now() - self._stats['current_session_start']

        return {
            'total_runtime': str(runtime),
            'current_session_duration': str(current_session),
            'sessions_completed': self._stats['sessions_completed'],
            'start_time': self._stats['start_time'].strftime('%Y-%m-%d %H:%M:%S'),
            'last_activity': self._stats['last_activity'].strftime('%Y-%m-%d %H:%M:%S')
        }

    def get_daily_stats(self, days: int = 7) -> List[Dict]:
        """获取最近几天的统计数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

                cursor.execute('''
                    SELECT * FROM daily_stats
                    WHERE date >= ?
                    ORDER BY date DESC
                ''', (start_date,))

                columns = [desc[0] for desc in cursor.description]
                results = []

                for row in cursor.fetchall():
                    result = dict(zip(columns, row))
                    # 移除id字段，只保留统计数据
                    result.pop('id', None)
                    results.append(result)

                return results

        except Exception as e:
            print(f"⚠️ 获取每日统计失败: {e}")
            return []

    def display_summary(self):
        """显示统计摘要"""
        runtime_info = self.get_runtime_info()
        total_interactions = self.get_total_interactions()

        print("\n" + "="*60)
        print("📊 抖音RPA运行统计摘要")
        print("="*60)
        print(f"📅 开始时间: {runtime_info['start_time']}")
        print(f"⏱️  总运行时间: {runtime_info['total_runtime']}")
        print(f"🔄 完成会话数: {runtime_info['sessions_completed']}")
        print(f"📺 观看视频: {self._stats['videos_watched']} 个")
        print(f"❤️  点赞操作: {self._stats['likes_given']} 次")
        print(f"💬 评论操作: {self._stats['comments_posted']} 次")
        print(f"⭐ 收藏操作: {self._stats['favorites_made']} 次")
        print(f"👥 关注操作: {self._stats['follows_added']} 次")
        print(f"🔍 搜索操作: {self._stats['searches_performed']} 次")
        print(f"❌ 遇到错误: {self._stats['errors_encountered']} 次")
        print(f"🎯 总交互数: {total_interactions} 次")

        if total_interactions > 0:
            success_rate = ((total_interactions - self._stats['errors_encountered']) /
                           (total_interactions + self._stats['errors_encountered'])) * 100
            print(f"✅ 成功率: {success_rate:.1f}%")

        # 计算平均数据
        if self._stats['videos_watched'] > 0:
            like_rate = (self._stats['likes_given'] / self._stats['videos_watched']) * 100
            comment_rate = (self._stats['comments_posted'] / self._stats['videos_watched']) * 100
            print(f"📈 点赞率: {like_rate:.1f}%")
            print(f"📝 评论率: {comment_rate:.1f}%")

        print("="*60)

    def export_data(self, export_path: str = None) -> str:
        """导出统计数据为JSON格式"""
        if export_path is None:
            export_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
            os.makedirs(export_dir, exist_ok=True)
            export_path = os.path.join(export_dir, f'douyin_stats_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')

        try:
            export_data = {
                'export_time': datetime.now().isoformat(),
                'runtime_info': self.get_runtime_info(),
                'current_stats': {
                    'sessions_completed': self._stats['sessions_completed'],
                    'videos_watched': self._stats['videos_watched'],
                    'likes_given': self._stats['likes_given'],
                    'comments_posted': self._stats['comments_posted'],
                    'favorites_made': self._stats['favorites_made'],
                    'follows_added': self._stats['follows_added'],
                    'searches_performed': self._stats['searches_performed'],
                    'errors_encountered': self._stats['errors_encountered'],
                    'total_interactions': self.get_total_interactions()
                },
                'daily_stats': self.get_daily_stats(30)  # 最近30天
            }

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)

            print(f"📤 数据已导出到: {export_path}")
            return export_path

        except Exception as e:
            print(f"❌ 数据导出失败: {e}")
            return None

    def reset_stats(self):
        """重置统计数据"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    # 清空所有表
                    cursor.execute('DELETE FROM daily_stats')
                    cursor.execute('DELETE FROM interaction_log')
                    cursor.execute('DELETE FROM runtime_state')
                    cursor.execute('DELETE FROM sessions')

                    conn.commit()

                # 重置内存统计
                self._stats = {
                    'sessions_completed': 0,
                    'videos_watched': 0,
                    'likes_given': 0,
                    'comments_posted': 0,
                    'favorites_made': 0,
                    'follows_added': 0,
                    'searches_performed': 0,
                    'errors_encountered': 0,
                    'start_time': datetime.now(),
                    'last_activity': datetime.now(),
                    'current_session_start': datetime.now(),
                    'current_session_type': None
                }

                print("📊 统计数据已重置")

            except Exception as e:
                print(f"❌ 重置统计数据失败: {e}")

# 全局统计器实例
_tracker = None

def get_tracker() -> InteractionTracker:
    """获取统计器实例"""
    global _tracker
    if _tracker is None:
        _tracker = InteractionTracker()
    return _tracker

def init_tracker(db_path: str = None) -> InteractionTracker:
    """初始化统计器"""
    global _tracker
    _tracker = InteractionTracker(db_path)
    return _tracker