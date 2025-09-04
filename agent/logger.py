#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一日志模块
支持线程安全和按日滚动的日志记录
"""

import os
import logging
import threading
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from typing import Optional, Dict, Any


class ThreadSafeLogger:
    """线程安全的日志记录器"""
    
    _instances: Dict[str, 'ThreadSafeLogger'] = {}
    _lock = threading.Lock()
    
    def __new__(cls, name: str, config: Optional[Dict[str, Any]] = None):
        """单例模式，确保同名logger只有一个实例"""
        with cls._lock:
            if name not in cls._instances:
                instance = super().__new__(cls)
                cls._instances[name] = instance
            return cls._instances[name]
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """初始化日志记录器"""
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.name = name
        self.config = config or {}
        self._setup_logger()
    
    def _setup_logger(self):
        """设置日志记录器"""
        # 获取配置参数
        log_mode = self.config.get('log_mode', 'INFO').upper()
        log_path = self.config.get('log_path', 'logs')
        log_name = self.config.get('log_name', 'agent')
        log_rotation = self.config.get('log_rotation', True)
        
        # 确保日志目录存在
        if not os.path.exists(log_path):
            os.makedirs(log_path, exist_ok=True)
        
        # 创建logger
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(getattr(logging, log_mode, logging.INFO))
        
        # 避免重复添加handler
        if self.logger.handlers:
            return
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_mode, logging.INFO))
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器
        if log_rotation:
            # 按日滚动的文件处理器
            log_file = os.path.join(log_path, f"{log_name}.log")
            file_handler = TimedRotatingFileHandler(
                log_file,
                when='midnight',
                interval=1,
                backupCount=30,  # 保留30天的日志
                encoding='utf-8'
            )
            # 设置滚动文件的命名格式
            file_handler.suffix = "%Y.%m.%d.log"
            file_handler.extMatch = r"^\d{4}\.\d{2}\.\d{2}\.log$"
        else:
            # 普通文件处理器
            log_file = os.path.join(log_path, f"{log_name}.log")
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
        
        file_handler.setLevel(getattr(logging, log_mode, logging.INFO))
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        self.logger.info(f"日志系统初始化完成 - 模式: {log_mode}, 路径: {log_path}, 滚动: {log_rotation}")
    
    def debug(self, message: str, *args, **kwargs):
        """记录DEBUG级别日志"""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """记录INFO级别日志"""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """记录WARNING级别日志"""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """记录ERROR级别日志"""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """记录CRITICAL级别日志"""
        self.logger.critical(message, *args, **kwargs)
    
    def log_task_event(self, event_type: str, task_id: str, **kwargs):
        """记录任务相关事件"""
        extra_info = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        message = f"[{event_type}] task_id={task_id}"
        if extra_info:
            message += f", {extra_info}"
        
        if event_type in ['任务新增', '任务修改', '任务删除']:
            self.info(message)
        elif event_type == '任务失败':
            self.error(message)
        else:
            self.debug(message)
    
    def log_thread_pool_status(self, **status_info):
        """记录线程池状态"""
        status_str = ", ".join([f"{k}={v}" for k, v in status_info.items()])
        self.debug(f"当前线程池 {status_str}")
    
    def get_logger(self) -> logging.Logger:
        """获取原始logger对象"""
        return self.logger


def get_logger(name: str = "agent", config: Optional[Dict[str, Any]] = None) -> ThreadSafeLogger:
    """获取线程安全的日志记录器实例"""
    return ThreadSafeLogger(name, config)


def setup_agent_logging(config: Dict[str, Any]) -> ThreadSafeLogger:
    """为Agent设置日志系统"""
    log_config = {
        'log_mode': config.get('log_mode', 'INFO'),
        'log_path': config.get('log_path', 'logs'),
        'log_name': config.get('log_name', 'agent'),
        'log_rotation': config.get('log_rotation', True)
    }
    
    return get_logger("agent", log_config)