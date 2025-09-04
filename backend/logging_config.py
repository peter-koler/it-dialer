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
    
    def __init__(self, log_file=None, log_level='INFO', when='midnight', interval=1, backup_count=30):
        """
        初始化日志配置
        
        Args:
            log_file: 日志文件路径，如果为None则只输出到控制台
            log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            when: 轮转时间单位 ('midnight' 表示每天午夜轮转)
            interval: 轮转间隔 (默认1天)
            backup_count: 保留的日志文件备份数量 (默认30天)
        """
        self.log_file = log_file
        self.log_level = log_level.upper()
        self.when = when
        self.interval = interval
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
            
            # 为当前日志文件添加日期后缀
            current_date = datetime.now().strftime('%Y.%m.%d')
            base_name, ext = os.path.splitext(self.log_file)
            dated_log_file = f"{base_name}.{current_date}{ext}"
            
            # 使用TimedRotatingFileHandler实现按天轮转
            file_handler = logging.handlers.TimedRotatingFileHandler(
                dated_log_file,
                when=self.when,
                interval=self.interval,
                backupCount=self.backup_count,
                encoding='utf-8',
                atTime=datetime.strptime('00:00:00', '%H:%M:%S').time()  # 每天午夜轮转
            )
            # 设置日志文件名后缀格式为 yyyy.mm.dd
            file_handler.suffix = '%Y.%m.%d'
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
        when = getattr(config, 'LOG_WHEN', 'midnight')
        interval = getattr(config, 'LOG_INTERVAL', 1)
        backup_count = getattr(config, 'LOG_BACKUP_COUNT', 30)
        
        return cls(log_file=log_file, log_level=log_level, 
                  when=when, interval=interval, backup_count=backup_count)


def setup_logging(log_file=None, log_level='INFO', when='midnight', interval=1, backup_count=30):
    """便捷函数：设置日志配置
    
    Args:
        log_file: 日志文件路径
        log_level: 日志级别
        when: 轮转时间单位
        interval: 轮转间隔
        backup_count: 保留的日志文件备份数量
    """
    config = LoggingConfig(log_file=log_file, log_level=log_level, 
                          when=when, interval=interval, backup_count=backup_count)
    config.setup_logging()
    return config