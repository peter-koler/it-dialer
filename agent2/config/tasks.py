#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
任务配置模块
提供拨测任务的配置界面和管理功能
"""

import json
import os
from typing import Dict, List, Any


class TaskConfigManager:
    """任务配置管理器"""
    
    def __init__(self, config_file: str = "tasks_config.json"):
        """
        初始化任务配置管理器
        
        Args:
            config_file: 任务配置文件路径
        """
        self.config_file = config_file
        self.tasks = []
        self.load_tasks()
    
    def load_tasks(self) -> None:
        """从配置文件加载任务"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.tasks = json.load(f)
            else:
                # 默认任务配置
                self.tasks = []
                self.save_tasks()
        except Exception as e:
            print(f"加载任务配置失败: {e}")
            self.tasks = []
    
    def save_tasks(self) -> None:
        """保存任务配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存任务配置失败: {e}")
            raise
    
    def add_task(self, task: Dict[str, Any]) -> bool:
        """
        添加新任务
        
        Args:
            task: 任务配置
            
        Returns:
            是否添加成功
        """
        try:
            # 检查任务ID是否已存在
            task_id = task.get("task_id")
            if self.get_task_by_id(task_id):
                print(f"任务ID {task_id} 已存在")
                return False
            
            self.tasks.append(task)
            self.save_tasks()
            return True
        except Exception as e:
            print(f"添加任务失败: {e}")
            return False
    
    def update_task(self, task_id: str, task_data: Dict[str, Any]) -> bool:
        """
        更新任务配置
        
        Args:
            task_id: 任务ID
            task_data: 新的任务配置
            
        Returns:
            是否更新成功
        """
        try:
            for i, task in enumerate(self.tasks):
                if task.get("task_id") == task_id:
                    self.tasks[i] = task_data
                    self.save_tasks()
                    return True
            return False
        except Exception as e:
            print(f"更新任务失败: {e}")
            return False
    
    def delete_task(self, task_id: str) -> bool:
        """
        删除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否删除成功
        """
        try:
            self.tasks = [task for task in self.tasks if task.get("task_id") != task_id]
            self.save_tasks()
            return True
        except Exception as e:
            print(f"删除任务失败: {e}")
            return False
    
    def get_task_by_id(self, task_id: str) -> Dict[str, Any] or None:
        """
        根据任务ID获取任务配置
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务配置，如果未找到返回None
        """
        for task in self.tasks:
            if task.get("task_id") == task_id:
                return task
        return None
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """
        获取所有任务配置
        
        Returns:
            任务配置列表
        """
        return self.tasks
    
    def get_tasks_by_type(self, task_type: str) -> List[Dict[str, Any]]:
        """
        根据任务类型获取任务配置
        
        Args:
            task_type: 任务类型
            
        Returns:
            指定类型的任务配置列表
        """
        return [task for task in self.tasks if task.get("type") == task_type]


def create_ping_task(task_id: str, target: str, count: int = 4, interval: int = 60) -> Dict[str, Any]:
    """
    创建ping任务配置
    
    Args:
        task_id: 任务ID
        target: 目标地址
        count: ping次数
        interval: 执行间隔(秒)
        
    Returns:
        任务配置
    """
    return {
        "task_id": task_id,
        "type": "ping",
        "target": target,
        "interval": interval,
        "params": {
            "count": count
        }
    }


def main():
    """测试函数"""
    # 创建任务配置管理器
    manager = TaskConfigManager()
    
    # 创建示例任务
    task1 = create_ping_task("task_1", "8.8.8.8", 4, 30)
    task2 = create_ping_task("task_2", "baidu.com", 4, 60)
    
    # 添加任务
    manager.add_task(task1)
    manager.add_task(task2)
    
    # 显示所有任务
    print("所有任务:")
    for task in manager.get_all_tasks():
        print(f"  {task}")


if __name__ == "__main__":
    main()