"""
统一日志管理模块
提供彩色控制台输出和文件记录功能
"""

import os
import sys
import atexit
import logging
from datetime import datetime
from typing import Optional
from logging.handlers import RotatingFileHandler

try:
    from colorlog import ColoredFormatter
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False
    print("⚠️ colorlog未安装，将使用标准日志格式")


class FlushingFileHandler(logging.FileHandler):
    """每次写入后立即刷新的文件处理器，覆盖模式"""
    
    def __init__(self, filename, mode='w', encoding='utf-8'):
        """mode='w' 覆盖旧文件"""
        super().__init__(filename, mode=mode, encoding=encoding)
    
    def emit(self, record):
        super().emit(record)
        self.flush()


class RobustLogger:
    """健壮的日志管理器"""
    
    _instances = {}
    
    def __new__(cls, name: str = "douyin_rpa", *args, **kwargs):
        """单例模式，每个名称只创建一个实例"""
        if name not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[name] = instance
        return cls._instances[name]
    
    def __init__(self, name: str = "douyin_rpa", 
                 log_dir: str = "logs",
                 level: int = logging.INFO,
                 max_bytes: int = 10*1024*1024,  # 10MB
                 backup_count: int = 5):
        """
        初始化日志器
        
        Args:
            name: 日志器名称
            log_dir: 日志目录
            level: 日志级别
            max_bytes: 单个日志文件最大大小
            backup_count: 保留的日志文件数量
        """
        # 避免重复初始化
        if hasattr(self, '_initialized'):
            return
        
        self.name = name
        self.log_dir = log_dir
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False
        
        # 确保日志目录存在
        os.makedirs(log_dir, exist_ok=True)
        
        # 清除已有的处理器
        self.logger.handlers.clear()
        
        # 添加文件处理器
        self._add_file_handler(max_bytes, backup_count)
        
        # 添加控制台处理器
        self._add_console_handler()
        
        # 添加错误日志处理器
        self._add_error_handler()
        
        self._initialized = True
        
        # 注册退出钩子，确保日志刷新
        atexit.register(self.flush_all)
        
        self.logger.info(f"日志系统初始化完成: {name}")
    
    def _add_file_handler(self, max_bytes: int, backup_count: int):
        """添加文件处理器（覆盖模式，固定文件名）"""
        # 固定文件名，每次运行覆盖旧文件
        log_file = os.path.join(self.log_dir, f"{self.name}.log")
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - [%(levelname)s] - '
            '%(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 使用覆盖模式 (mode='w')
        file_handler = FlushingFileHandler(log_file, mode='w')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
    
    def _add_console_handler(self):
        """添加彩色控制台处理器"""
        if HAS_COLORLOG:
            console_formatter = ColoredFormatter(
                '%(log_color)s%(asctime)s - %(name)s - [%(levelname)s]%(reset)s - '
                '%(cyan)s%(filename)s:%(lineno)d%(reset)s - %(message)s',
                datefmt='%H:%M:%S',
                log_colors={
                    'DEBUG': 'white',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
        else:
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - [%(levelname)s] - '
                '%(filename)s:%(lineno)d - %(message)s',
                datefmt='%H:%M:%S'
            )
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
    
    def _add_error_handler(self):
        """添加专门的错误日志处理器"""
        error_log_file = os.path.join(self.log_dir, "error.log")
        
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - [%(levelname)s] - '
            '%(filename)s:%(lineno)d - %(funcName)s()\n'
            '%(message)s\n'
            '----------------------------------------\n',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(error_formatter)
        self.logger.addHandler(error_handler)
    
    def debug(self, msg: str, *args, **kwargs):
        """调试日志"""
        self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        """信息日志"""
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        """警告日志"""
        self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, exc_info: bool = True, **kwargs):
        """错误日志"""
        self.logger.error(msg, *args, exc_info=exc_info, **kwargs)
    
    def critical(self, msg: str, *args, exc_info: bool = True, **kwargs):
        """严重错误日志"""
        self.logger.critical(msg, *args, exc_info=exc_info, **kwargs)
    
    def exception(self, msg: str, *args, **kwargs):
        """异常日志（自动包含堆栈跟踪）"""
        self.logger.exception(msg, *args, **kwargs)
    
    def set_level(self, level: int):
        """设置日志级别"""
        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, RotatingFileHandler):
                handler.setLevel(level)
    
    def flush_all(self):
        """强制刷新所有日志处理器"""
        for handler in self.logger.handlers:
            try:
                handler.flush()
            except Exception:
                pass
    
    def flush(self):
        """刷新日志（每次重要操作后调用）"""
        self.flush_all()


# 全局日志实例
_global_logger: Optional[RobustLogger] = None


def get_logger(name: str = "douyin_rpa") -> RobustLogger:
    """
    获取日志器实例
    
    Args:
        name: 日志器名称
        
    Returns:
        RobustLogger: 日志器实例
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = RobustLogger(name)
    return _global_logger


def setup_logger(name: str = "douyin_rpa", 
                level: int = logging.INFO,
                log_dir: str = "logs") -> RobustLogger:
    """
    设置并获取日志器
    
    Args:
        name: 日志器名称
        level: 日志级别
        log_dir: 日志目录
        
    Returns:
        RobustLogger: 日志器实例
    """
    global _global_logger
    _global_logger = RobustLogger(name, log_dir=log_dir, level=level)
    return _global_logger


# 便捷的模块级日志函数
def debug(msg: str, *args, **kwargs):
    """模块级调试日志"""
    get_logger().debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs):
    """模块级信息日志"""
    get_logger().info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs):
    """模块级警告日志"""
    get_logger().warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs):
    """模块级错误日志"""
    get_logger().error(msg, *args, **kwargs)


def critical(msg: str, *args, **kwargs):
    """模块级严重错误日志"""
    get_logger().critical(msg, *args, **kwargs)


def exception(msg: str, *args, **kwargs):
    """模块级异常日志"""
    get_logger().exception(msg, *args, **kwargs)


def set_log_level(level_name: str):
    """
    动态设置日志级别
    
    Args:
        level_name: 日志级别名称 ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    """
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    level = level_map.get(level_name.upper(), logging.INFO)
    get_logger().set_level(level)
    print(f"📋 日志级别已设置为: {level_name.upper()}")

