#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ping插件
实现具体的ping拨测任务
"""

import subprocess
import platform
import re
import time
import logging
from typing import Dict, Any

# 插件名称
PLUGIN_NAME = "ping"

# 配置日志
logger = logging.getLogger(__name__)

def execute(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    执行ping任务
    
    Args:
        task: 任务配置
            {
                "task_id": "task_1",
                "type": "ping",
                "target": "8.8.8.8",
                "params": {
                    "count": 4
                }
            }
            
    Returns:
        执行结果
    """
    target = task.get("target", "8.8.8.8")
    count = task.get("params", {}).get("count", 4)
    task_id = task.get("task_id", "unknown")
    
    logger.info(f"开始执行Ping任务 {task_id}: 目标={target}, 次数={count}")
    
    try:
        # 根据操作系统选择ping命令
        if platform.system().lower() == "windows":
            cmd = ["ping", "-n", str(count), target]
        else:
            cmd = ["ping", "-c", str(count), target]
        
        logger.info(f"执行命令: {' '.join(cmd)}")
        
        # 执行ping命令
        start_time = time.time()
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        end_time = time.time()
        
        logger.info(f"Ping命令执行完成，耗时: {end_time - start_time:.2f}秒")
        
        # 解析ping结果
        ping_result = parse_ping_output(result.stdout, result.stderr)
        ping_result["execution_time"] = end_time - start_time
        ping_result["target"] = target
        
        # 记录详细输出（按error级别记录）
        logger.error(f"任务 {task_id} Ping详细输出 - stdout: {result.stdout}")
        logger.error(f"任务 {task_id} Ping详细输出 - stderr: {result.stderr}")
        
        return ping_result
        
    except subprocess.TimeoutExpired as e:
        error_msg = f"Ping命令执行超时 (>{e.timeout}秒)"
        logger.error(f"任务 {task_id} 执行失败: {error_msg}")
        return {
            "status": "timeout",
            "message": error_msg,
            "target": target
        }
    except Exception as e:
        error_msg = str(e)
        logger.error(f"任务 {task_id} 执行失败: {error_msg}")
        return {
            "status": "error",
            "message": error_msg,
            "target": target
        }

def parse_ping_output(stdout: str, stderr: str) -> Dict[str, Any]:
    """
    解析ping命令输出
    
    Args:
        stdout: 标准输出
        stderr: 错误输出
        
    Returns:
        解析结果
    """
    result = {
        "status": "unknown",
        "packet_sent": 0,
        "packet_received": 0,
        "packet_loss": 0,
        "rtt_min": 0,
        "rtt_avg": 0,
        "rtt_max": 0
    }
    
    if stderr:
        result["status"] = "error"
        result["message"] = stderr.strip()
        logger.error(f"Ping错误输出: {stderr.strip()}")
        return result
    
    if not stdout:
        result["status"] = "error"
        result["message"] = "无输出"
        logger.error("Ping无输出")
        return result
    
    # 尝试解析数据包统计信息
    # Linux格式: 4 packets transmitted, 4 received, 0% packet loss
    # 或者: 4 packets transmitted, 4 packets received, 0.0% packet loss
    packet_pattern = r"(\d+) packets transmitted, (\d+) (?:received|packets received), ([\d.]+)% packet loss"
    packet_match = re.search(packet_pattern, stdout)
    
    if packet_match:
        result["packet_sent"] = int(packet_match.group(1))
        result["packet_received"] = int(packet_match.group(2))
        result["packet_loss"] = float(packet_match.group(3))
        result["status"] = "success" if float(packet_match.group(3)) < 100 else "failed"
    elif "Sent =" in stdout:
        # Windows格式
        packet_match = re.search(r"Sent = (\d+), Received = (\d+), Lost = (\d+)", stdout)
        if packet_match:
            result["packet_sent"] = int(packet_match.group(1))
            result["packet_received"] = int(packet_match.group(2))
            lost = int(packet_match.group(3))
            result["packet_loss"] = int((lost / int(packet_match.group(1))) * 100) if int(packet_match.group(1)) > 0 else 0
            result["status"] = "success" if lost < int(packet_match.group(1)) else "failed"
    
    # 尝试解析RTT统计信息
    # Linux格式: rtt min/avg/max/mdev = 10.0/15.5/20.0/2.0 ms
    # 或者: round-trip min/avg/max/stddev = 12.350/13.568/15.387/1.228 ms
    rtt_pattern = r"(?:rtt|round-trip) min/avg/max(?:/mdev|/stddev) = ([\d.]+)/([\d.]+)/([\d.]+)(?:/[\d.]+)? ms"
    rtt_match = re.search(rtt_pattern, stdout)
    
    if rtt_match:
        result["rtt_min"] = float(rtt_match.group(1))
        result["rtt_avg"] = float(rtt_match.group(2))
        result["rtt_max"] = float(rtt_match.group(3))
    elif "Minimum =" in stdout:
        # Windows格式
        rtt_match = re.search(r"Minimum = (\d+)ms, Maximum = (\d+)ms, Average = (\d+)ms", stdout)
        if rtt_match:
            result["rtt_min"] = float(rtt_match.group(1))
            result["rtt_max"] = float(rtt_match.group(2))
            result["rtt_avg"] = float(rtt_match.group(3))
    
    logger.info(f"Ping解析结果: {result}")
    return result