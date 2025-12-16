"""
抖音RPA项目配置中心
支持热更新和反检测措施
"""

import os
import json
import random
import time
from datetime import datetime, time as dt_time
from typing import Dict, Any, List
import threading

class HotReloadConfig:
    """支持热更新的配置管理器（含后台监听）"""

    def __init__(self, config_file: str = None):
        self.config_file = config_file or os.path.join(os.path.dirname(__file__), 'runtime_config.json')
        self._config = {}
        self._lock = threading.Lock()
        self._last_modified = 0
        self._watch_thread = None
        self._watching = False
        self._callbacks = []  # 配置变化回调函数列表
        self.load_config()
    
    def start_watching(self, interval: float = 5.0):
        """启动后台配置监听线程"""
        if self._watching:
            return
        self._watching = True
        self._watch_thread = threading.Thread(target=self._watch_loop, args=(interval,), daemon=True)
        self._watch_thread.start()
        print(f"📡 配置监听已启动（间隔 {interval}s）")
    
    def stop_watching(self):
        """停止后台配置监听"""
        self._watching = False
        if self._watch_thread:
            self._watch_thread.join(timeout=2)
            self._watch_thread = None
        print("⏹️ 配置监听已停止")
    
    def _watch_loop(self, interval: float):
        """配置监听循环"""
        while self._watching:
            if self.auto_reload():
                for callback in self._callbacks:
                    try:
                        callback(self._config)
                    except Exception as e:
                        print(f"配置回调执行失败: {e}")
            time.sleep(interval)
    
    def add_callback(self, callback):
        """添加配置变化回调函数"""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                self._last_modified = os.path.getmtime(self.config_file)
        except Exception as e:
            print(f"配置文件加载失败: {e}")
            self._config = self.get_default_config()

    def auto_reload(self):
        """自动重载配置（如果文件被修改）"""
        try:
            if os.path.exists(self.config_file):
                current_modified = os.path.getmtime(self.config_file)
                if current_modified > self._last_modified:
                    with self._lock:
                        old_config = self._config.copy()
                        self.load_config()
                        print(f"配置已热更新: {datetime.now()}")
                        return True
        except Exception as e:
            print(f"配置热更新失败: {e}")
        return False

    def get(self, key: str, default=None):
        """获取配置值"""
        self.auto_reload()
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any):
        """设置配置值"""
        self.auto_reload()
        with self._lock:
            keys = key.split('.')
            config = self._config
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            config[keys[-1]] = value
            self.save_config()

    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            self._last_modified = os.path.getmtime(self.config_file)
        except Exception as e:
            print(f"配置保存失败: {e}")

    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "appium": {
                "server_url": "http://127.0.0.1:4723",
                "caps": {
                    "platformName": "Android",
                    "deviceName": "Android Device",
                    "appPackage": "com.ss.android.ugc.aweme",
                    "appActivity": ".main.MainActivity",
                    "automationName": "UiAutomator2",
                    "noReset": True,
                    "fullReset": False,
                    "unicodeKeyboard": True,
                    "resetKeyboard": True,
                    "newCommandTimeout": 600,
                    "commandTimeouts": {"default": 60000}
                }
            },
            "sessions": {
                "for_you_min_videos": 15,
                "for_you_max_videos": 25,
                "search_min_videos": 30,
                "search_max_videos": 50
            },
            "behavior": {
                "for_you_like_prob": 0.1,
                "search_like_prob": 0.8,
                "search_comment_prob": 0.2,
                "search_favorite_prob": 0.15,
                "search_follow_prob": 0.1
            },
            "timing": {
                "watch_time_min": 7,
                "watch_time_max": 15,
                "action_delay_min": 1,
                "action_delay_max": 3
            },
            "anti_detection": {
                "random_session_interval": True,
                "min_break_minutes": 5,
                "max_break_minutes": 20,
                "daily_active_hours": [9, 10, 11, 14, 15, 16, 19, 20, 21],
                "simulate_human_errors": True,
                "random_scroll_speed": True,
                "variable_touch_positions": True
            },
            "recovery": {
                "max_retry_attempts": 3,
                "network_timeout": 30,
                "element_wait_timeout": 10,
                "app_restart_threshold": 5
            },
            "logging": {
                "level": "INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
                "console_level": "INFO",
                "file_level": "DEBUG"
            },
            "llm": {
                "provider": "dashscope",
                "api_key": "",
                "model": "qwen-turbo",
                "max_reply_length": 12,
                "system_prompt": "你是一个抖音评论区的热心用户，需要回复其他用户的评论。\n\n回复要求：\n1. 字数严格控制在12字以内\n2. 语气亲切自然，像朋友聊天\n3. 巧妙引导对方看你的主页/头像，但不要太直接\n4. 不要用“私信”这类词，容易被限流\n5. 可以用：看我主页/我头像有/我那边有/我用过xx挺好 等表达",
                "user_prompt_template": "用户评论：\"{comment}\"\n\n请用不超过12个字回复这条评论，引导对方查看你的主页。直接输出回复内容，不要任何解释。",
                "fallback_replies": ["看我主页有分享~", "我那有同款哦", "头像找我聊~", "主页有详细的"]
            }
        }

# 全局配置实例
config = HotReloadConfig()

# Appium配置
DOUYIN_CAPS = config.get('appium.caps', {})
APPIUM_SERVER_URL = config.get('appium.server_url', 'http://127.0.0.1:4723')

# 会话节奏控制
SESSION_FOR_YOU_MIN_VIDEOS = config.get('sessions.for_you_min_videos', 15)
SESSION_FOR_YOU_MAX_VIDEOS = config.get('sessions.for_you_max_videos', 25)
SESSION_SEARCH_MIN_VIDEOS = config.get('sessions.search_min_videos', 30)
SESSION_SEARCH_MAX_VIDEOS = config.get('sessions.search_max_videos', 50)

# 行为概率
FOR_YOU_LIKE_PROB = config.get('behavior.for_you_like_prob', 0.55)
FOR_YOU_COMMENT_PROB = config.get('behavior.for_you_comment_prob', 0.33)
FOR_YOU_FAVORITE_PROB = config.get('behavior.for_you_favorite_prob', 0.33)
FOR_YOU_FOLLOW_PROB = config.get('behavior.for_you_follow_prob', 0.33)
SEARCH_LIKE_PROB = config.get('behavior.search_like_prob', 0.8)
SEARCH_COMMENT_PROB = config.get('behavior.search_comment_prob', 0.2)
SEARCH_FAVORITE_PROB = config.get('behavior.search_favorite_prob', 0.15)
SEARCH_FOLLOW_PROB = config.get('behavior.search_follow_prob', 0.1)

# 仿真延迟
WATCH_TIME_MIN = config.get('timing.watch_time_min', 7)
WATCH_TIME_MAX = config.get('timing.watch_time_max', 15)
ACTION_DELAY_MIN = config.get('timing.action_delay_min', 1)
ACTION_DELAY_MAX = config.get('timing.action_delay_max', 3)

# 反检测配置
ANTI_DETECTION_CONFIG = config.get('anti_detection', {})

# 恢复配置
RECOVERY_CONFIG = config.get('recovery', {})

# 日志配置
LOG_LEVEL = config.get('logging.level', 'INFO')
LOG_CONSOLE_LEVEL = config.get('logging.console_level', 'INFO')
LOG_FILE_LEVEL = config.get('logging.file_level', 'DEBUG')

# LLM配置
LLM_PROVIDER = config.get('llm.provider', 'dashscope')
LLM_API_KEY = config.get('llm.api_key', '')
LLM_MODEL = config.get('llm.model', 'qwen-turbo')
LLM_MAX_REPLY_LENGTH = config.get('llm.max_reply_length', 12)
LLM_SYSTEM_PROMPT = config.get('llm.system_prompt', '')
LLM_USER_PROMPT_TEMPLATE = config.get('llm.user_prompt_template', '用户评论："{comment}"\n请用不超过12个字回复。')
LLM_FALLBACK_REPLIES = config.get('llm.fallback_replies', ['看我主页有分享~', '我那有同款哦'])

def _on_config_changed(new_config: Dict[str, Any]):
    """配置变化回调 - 动态更新日志级别等"""
    try:
        from src.logger import set_log_level
        new_level = new_config.get('logging', {}).get('level', 'INFO')
        set_log_level(new_level)
    except Exception as e:
        print(f"配置回调执行失败: {e}")

# 注册配置变化回调
config.add_callback(_on_config_changed)

def is_active_hour() -> bool:
    """检查当前是否为活跃时间"""
    current_hour = datetime.now().hour
    active_hours = ANTI_DETECTION_CONFIG.get('daily_active_hours', list(range(9, 22)))
    return current_hour in active_hours

def should_take_break() -> bool:
    """判断是否应该休息"""
    if not ANTI_DETECTION_CONFIG.get('random_session_interval', True):
        return False

    # 可以根据运行时长、操作次数等因素判断
    return random.random() < 0.1  # 10%概率休息

def get_break_duration() -> float:
    """获取休息时长（分钟）"""
    min_minutes = ANTI_DETECTION_CONFIG.get('min_break_minutes', 5)
    max_minutes = ANTI_DETECTION_CONFIG.get('max_break_minutes', 20)
    # 支持浮点数休息时间
    if isinstance(min_minutes, (int, float)) and isinstance(max_minutes, (int, float)):
        return random.uniform(float(min_minutes), float(max_minutes))
    return random.randint(int(min_minutes), int(max_minutes))

def reload_settings():
    """手动重载配置"""
    global config, DOUYIN_CAPS, APPIUM_SERVER_URL
    global SESSION_FOR_YOU_MIN_VIDEOS, SESSION_FOR_YOU_MAX_VIDEOS
    global SESSION_SEARCH_MIN_VIDEOS, SESSION_SEARCH_MAX_VIDEOS
    global FOR_YOU_LIKE_PROB, FOR_YOU_COMMENT_PROB, FOR_YOU_FAVORITE_PROB, FOR_YOU_FOLLOW_PROB
    global SEARCH_LIKE_PROB, SEARCH_COMMENT_PROB, SEARCH_FAVORITE_PROB, SEARCH_FOLLOW_PROB
    global WATCH_TIME_MIN, WATCH_TIME_MAX, ACTION_DELAY_MIN, ACTION_DELAY_MAX
    global ANTI_DETECTION_CONFIG, RECOVERY_CONFIG

    config.load_config()

    DOUYIN_CAPS = config.get('appium.caps', {})
    APPIUM_SERVER_URL = config.get('appium.server_url', 'http://127.0.0.1:4723')

    SESSION_FOR_YOU_MIN_VIDEOS = config.get('sessions.for_you_min_videos', 15)
    SESSION_FOR_YOU_MAX_VIDEOS = config.get('sessions.for_you_max_videos', 25)
    SESSION_SEARCH_MIN_VIDEOS = config.get('sessions.search_min_videos', 30)
    SESSION_SEARCH_MAX_VIDEOS = config.get('sessions.search_max_videos', 50)

    FOR_YOU_LIKE_PROB = config.get('behavior.for_you_like_prob', 0.55)
    FOR_YOU_COMMENT_PROB = config.get('behavior.for_you_comment_prob', 0.33)
    FOR_YOU_FAVORITE_PROB = config.get('behavior.for_you_favorite_prob', 0.33)
    FOR_YOU_FOLLOW_PROB = config.get('behavior.for_you_follow_prob', 0.33)
    SEARCH_LIKE_PROB = config.get('behavior.search_like_prob', 0.8)
    SEARCH_COMMENT_PROB = config.get('behavior.search_comment_prob', 0.2)
    SEARCH_FAVORITE_PROB = config.get('behavior.search_favorite_prob', 0.15)
    SEARCH_FOLLOW_PROB = config.get('behavior.search_follow_prob', 0.1)

    WATCH_TIME_MIN = config.get('timing.watch_time_min', 7)
    WATCH_TIME_MAX = config.get('timing.watch_time_max', 15)
    ACTION_DELAY_MIN = config.get('timing.action_delay_min', 1)
    ACTION_DELAY_MAX = config.get('timing.action_delay_max', 3)

    ANTI_DETECTION_CONFIG = config.get('anti_detection', {})
    RECOVERY_CONFIG = config.get('recovery', {})

# 初始化时保存默认配置
if not os.path.exists(config.config_file):
    config.save_config()