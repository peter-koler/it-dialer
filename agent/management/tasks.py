#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
任务管理模块
展示Agent上报的拨测数据
"""

import json
import os
from typing import Dict, List, Any
from datetime import datetime


class TaskResultManager:
    """任务结果管理器"""
    
    def __init__(self, results_file: str = "task_results.json"):
        """
        初始化任务结果管理器
        
        Args:
            results_file: 任务结果存储文件
        """
        self.results_file = results_file
        self.results = []
        self.load_results()
    
    def load_results(self) -> None:
        """从文件加载任务结果"""
        try:
            if os.path.exists(self.results_file):
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    self.results = json.load(f)
            else:
                self.results = []
        except Exception as e:
            print(f"加载任务结果失败: {e}")
            self.results = []
    
    def save_results(self) -> None:
        """保存任务结果到文件"""
        try:
            # 只保留最近1000条记录
            if len(self.results) > 1000:
                self.results = self.results[-1000:]
            
            with open(self.results_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存任务结果失败: {e}")
    
    def add_result(self, result: Dict[str, Any]) -> None:
        """
        添加任务执行结果
        
        Args:
            result: 任务执行结果
        """
        try:
            # 添加时间戳
            result["record_time"] = datetime.now().isoformat()
            self.results.append(result)
            self.save_results()
        except Exception as e:
            print(f"添加任务结果失败: {e}")
    
    def get_results(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取任务执行结果
        
        Args:
            limit: 返回结果数量限制
            
        Returns:
            任务执行结果列表
        """
        # 返回最新的结果
        return self.results[-limit:] if self.results else []
    
    def get_results_by_task_id(self, task_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        根据任务ID获取执行结果
        
        Args:
            task_id: 任务ID
            limit: 返回结果数量限制
            
        Returns:
            指定任务的执行结果列表
        """
        filtered_results = [r for r in self.results if r.get("task_id") == task_id]
        return filtered_results[-limit:] if filtered_results else []
    
    def get_results_by_time_range(self, start_time: str, end_time: str) -> List[Dict[str, Any]]:
        """
        根据时间范围获取执行结果
        
        Args:
            start_time: 开始时间 (ISO格式)
            end_time: 结束时间 (ISO格式)
            
        Returns:
            时间范围内的执行结果列表
        """
        try:
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
            
            filtered_results = []
            for result in self.results:
                record_time = datetime.fromisoformat(result.get("record_time", ""))
                if start_dt <= record_time <= end_dt:
                    filtered_results.append(result)
            
            return filtered_results
        except Exception as e:
            print(f"按时间范围筛选结果失败: {e}")
            return []


def format_result(result: Dict[str, Any]) -> str:
    """
    格式化任务执行结果用于显示
    
    Args:
        result: 任务执行结果
        
    Returns:
        格式化后的字符串
    """
    task_id = result.get("task_id", "Unknown")
    status = result.get("status", "Unknown")
    record_time = result.get("record_time", "Unknown")
    
    if status == "success":
        result_data = result.get("result", {})
        target = result_data.get("target", "Unknown")
        packet_loss = result_data.get("packet_loss", 0)
        rtt_avg = result_data.get("rtt_avg", 0)
        
        return (f"[{record_time}] 任务 {task_id} 执行成功\n"
                f"  目标: {target}\n"
                f"  丢包率: {packet_loss}%\n"
                f"  平均延迟: {rtt_avg}ms")
    else:
        message = result.get("message", "Unknown error")
        return (f"[{record_time}] 任务 {task_id} 执行失败\n"
                f"  状态: {status}\n"
                f"  错误信息: {message}")


def main():
    """测试函数"""
    # 创建任务结果管理器
    manager = TaskResultManager()
    
    # 模拟添加一些结果
    result1 = {
        "task_id": "task_1",
        "status": "success",
        "result": {
            "target": "8.8.8.8",
            "packet_sent": 4,
            "packet_received": 4,
            "packet_loss": 0,
            "rtt_min": 10.5,
            "rtt_avg": 15.2,
            "rtt_max": 20.1
        }
    }
    
    result2 = {
        "task_id": "task_2",
        "status": "error",
        "message": "网络不可达"
    }
    
    # 添加结果
    manager.add_result(result1)
    manager.add_result(result2)
    
    # 显示结果
    print("任务执行结果:")
    for result in manager.get_results():
        print(format_result(result))
        print("-" * 50)


if __name__ == "__main__":
    main()