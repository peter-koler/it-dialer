#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TCP插件
实现TCP端口连通性拨测任务
"""

import socket
import time
import logging
from typing import Dict, Any

# 插件名称
PLUGIN_NAME = "tcp"

# 配置日志
logger = logging.getLogger(__name__)


def execute(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    执行TCP端口连通性检测任务
    
    Args:
        task: 任务配置
            {
                "task_id": "task_1",
                "type": "tcp",
                "target": "example.com:80",
                "params": {
                    "timeout": 5
                }
            }
            
    Returns:
        执行结果
    """
    target = task.get("target", "localhost:80")
    timeout = task.get("params", {}).get("timeout", 5)
    task_id = task.get("task_id", "unknown")
    
    logger.info(f"开始执行TCP任务 {task_id}: 目标={target}, 超时={timeout}秒")
    
    # 解析目标地址和端口
    try:
        if ':' in target:
            host, port_str = target.rsplit(':', 1)
            port = int(port_str)
        else:
            host = target
            port = 80  # 默认端口
    except ValueError as e:
        error_msg = f"目标地址格式错误: {target}"
        logger.error(f"任务 {task_id} 执行失败: {error_msg}")
        return {
            "status": "error",
            "message": error_msg,
            "target": target
        }
    
    try:
        # 记录开始时间
        start_time = time.time()
        
        # 创建socket连接
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        # 尝试连接
        result = sock.connect_ex((host, port))
        sock.close()
        
        # 记录结束时间
        end_time = time.time()
        execution_time = end_time - start_time
        
        logger.info(f"TCP连接测试完成，耗时: {execution_time:.2f}秒")
        
        # 构造结果
        tcp_result = {
            "status": "success" if result == 0 else "failed",
            "connected": result == 0,
            "target": target,
            "host": host,
            "port": port,
            "execution_time": execution_time,
            "return_code": result
        }
        
        if result != 0:
            tcp_result["message"] = f"连接失败，返回码: {result}"
        
        logger.info(f"任务 {task_id} TCP检测结果: {tcp_result}")
        return tcp_result
        
    except socket.gaierror as e:
        error_msg = f"域名解析失败: {str(e)}"
        logger.error(f"任务 {task_id} 执行失败: {error_msg}")
        return {
            "status": "error",
            "message": error_msg,
            "target": target,
            "host": host,
            "port": port
        }
    except Exception as e:
        error_msg = str(e)
        logger.error(f"任务 {task_id} 执行失败: {error_msg}")
        return {
            "status": "error",
            "message": error_msg,
            "target": target,
            "host": host,
            "port": port
        }