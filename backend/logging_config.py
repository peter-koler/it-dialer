#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志配置模块
提供统一的日志配置功能，支持文件输出和日志级别设置
"""

import logging
import logging.handlers
import os
from datetime import datetime


class LoggingConfig:
    """日志配置类"""
    
    def __init__(self, log_file=None, log_level='INFO', max_bytes=10*1024*1024, backup_count=5):
        """
        初始化日志配置
        
        Args:
            log_file: 日志文件路径，如果为None则只输出到控制台
            log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            max_bytes: 单个日志文件最大字节数 (默认10MB)
            backup_count: 保留的日志文件备份数量 (默认5个)
        """
        self.log_file = log_file
        self.log_level = log_level.upper()
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.logger_initialized = False
    
    def setup_logging(self):
        """设置日志配置"""
        if self.logger_initialized:
            return
            
        # 获取根日志记录器
        root_logger = logging.getLogger()
        
        # 清除现有的处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 设置日志级别
        numeric_level = getattr(logging, self.log_level, logging.INFO)
        root_logger.setLevel(numeric_level)
        
        # 创建日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # 文件处理器（如果指定了日志文件）
        if self.log_file:
            # 确保日志文件目录存在
            log_dir = os.path.dirname(self.log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            # 使用RotatingFileHandler实现日志轮转
            file_handler = logging.handlers.RotatingFileHandler(
                self.log_file,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
            print(f"日志配置完成 - 文件: {self.log_file}, 级别: {self.log_level}")
        else:
            print(f"日志配置完成 - 仅控制台输出, 级别: {self.log_level}")
        
        self.logger_initialized = True
    
    @classmethod
    def from_config(cls, config):
        """从配置对象创建日志配置
        
        Args:
            config: 配置对象，应包含LOG_FILE和LOG_LEVEL属性
            
        Returns:
            LoggingConfig实例
        """
        log_file = getattr(config, 'LOG_FILE', None)
        log_level = getattr(config, 'LOG_LEVEL', 'INFO')
        max_bytes = getattr(config, 'LOG_MAX_BYTES', 10*1024*1024)
        backup_count = getattr(config, 'LOG_BACKUP_COUNT', 5)
        
        return cls(log_file=log_file, log_level=log_level, 
                  max_bytes=max_bytes, backup_count=backup_count)


def setup_logging(log_file=None, log_level='INFO'):
    """便捷函数：设置日志配置
    
    Args:
        log_file: 日志文件路径
        log_level: 日志级别
    """
    config = LoggingConfig(log_file=log_file, log_level=log_level)
    config.setup_logging()
    return config