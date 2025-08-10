#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
拨测Agent主模块
功能：支持插件加载，从系统配置中获取拨测任务，并执行任务
"""

import os
import sys
import json
import importlib
import time
import logging
import requests
import socket
from typing import Dict, List, Any
from pathlib import Path
from datetime import datetime
from threading import Thread

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DialerAgent:
    """拨测Agent类"""
    
    def __init__(self, config_path: str = "agent_config.json"):
        """
        初始化拨测Agent
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = {}
        self.plugins = {}
        self.tasks = []
        self.agent_info = {}
        
        # 加载配置
        self.load_config()
        
        # 设置日志级别
        log_level = self.config.get("log_level", "INFO")
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        logging.getLogger().setLevel(numeric_level)
        logger.info(f"日志级别设置为: {log_level}")
        
        # 获取agent信息
        self.collect_agent_info()
        
        # 加载插件
        self.load_plugins()
        
        # 心跳线程
        self.heartbeat_thread = None
        self.running = False
    
    def collect_agent_info(self):
        """收集agent信息"""
        self.agent_info = {
            "agent_id": self.config.get("agent_id", "default_agent"),
            "agent_area": self.config.get("agent_area", "default_area"),
            "ip_address": self.get_local_ip(),
            "hostname": socket.gethostname()
        }
        logger.info(f"Agent信息: {self.agent_info}")
    
    def get_local_ip(self):
        """获取本机IP地址"""
        try:
            # 创建一个UDP连接来获取本机IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            logger.error(f"获取本机IP失败: {e}")
            return "127.0.0.1"
    
    def load_config(self) -> None:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                # 默认配置
                self.config = {
                    "agent_id": "default_agent",
                    "server_url": "http://localhost:5000",
                    "plugins_dir": "plugins",
                    "report_interval": 60,
                    "log_level": "INFO",
                    "agent_area": "default_area"
                }
                self.save_config()
                
            logger.info("配置加载成功")
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            raise
    
    def save_config(self) -> None:
        """保存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info("配置保存成功")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def load_plugins(self) -> None:
        """加载插件"""
        plugins_dir = self.config.get("plugins_dir", "plugins")
        
        # 确保插件目录存在
        if not os.path.exists(plugins_dir):
            os.makedirs(plugins_dir)
            logger.info(f"创建插件目录: {plugins_dir}")
        
        # 添加插件目录到Python路径
        sys.path.insert(0, plugins_dir)
        
        # 查找插件文件
        plugin_files = Path(plugins_dir).glob("*.py")
        
        for plugin_file in plugin_files:
            if plugin_file.name.startswith("__"):
                continue
                
            try:
                module_name = plugin_file.stem
                # 动态导入插件模块
                module = importlib.import_module(module_name)
                
                # 检查模块是否有必要的属性
                if hasattr(module, 'PLUGIN_NAME') and hasattr(module, 'execute'):
                    self.plugins[module.PLUGIN_NAME] = module
                    logger.info(f"插件加载成功: {module.PLUGIN_NAME}")
                else:
                    logger.warning(f"插件 {module_name} 缺少必要属性，跳过加载")
                    
            except Exception as e:
                logger.error(f"加载插件 {plugin_file.name} 失败: {e}")
        
        logger.info(f"插件加载完成，共加载 {len(self.plugins)} 个插件")
    
    def register_agent(self):
        """注册agent到服务器"""
        try:
            server_url = self.config.get("server_url", "http://localhost:5000")
            response = requests.post(
                f"{server_url}/api/v1/nodes/register",
                headers={"Content-Type": "application/json"},
                json=self.agent_info
            )
            
            if response.status_code == 200 or response.status_code == 201:
                logger.info("Agent注册成功")
                return True
            else:
                logger.error(f"Agent注册失败: status_code={response.status_code}, response={response.text}")
                return False
        except Exception as e:
            logger.error(f"Agent注册时发生异常: {e}")
            return False
    
    def send_heartbeat(self):
        """发送心跳信息到服务器"""
        try:
            server_url = self.config.get("server_url", "http://localhost:5000")
            response = requests.post(
                f"{server_url}/api/v1/nodes/heartbeat",
                headers={"Content-Type": "application/json"},
                json={
                    "agent_id": self.agent_info["agent_id"],
                    "timestamp": datetime.fromtimestamp(time.time()).isoformat()
                }
            )
            
            if response.status_code == 200:
                logger.debug("心跳信息发送成功")
                return True
            else:
                logger.error(f"心跳信息发送失败: status_code={response.status_code}, response={response.text}")
                return False
        except Exception as e:
            logger.error(f"发送心跳信息时发生异常: {e}")
            return False
    
    def heartbeat_worker(self):
        """心跳工作线程"""
        while self.running:
            self.send_heartbeat()
            # 每5分钟发送一次心跳
            time.sleep(300)
    
    def start_heartbeat(self):
        """启动心跳线程"""
        self.running = True
        self.heartbeat_thread = Thread(target=self.heartbeat_worker)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()
        logger.info("心跳线程已启动")
    
    def stop_heartbeat(self):
        """停止心跳线程"""
        self.running = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join()
        logger.info("心跳线程已停止")
    
    def get_tasks(self) -> List[Dict[str, Any]]:
        """
        从系统配置中获取拨测任务
        从后端API获取任务而不是使用模拟数据
        """
        try:
            server_url = self.config.get("server_url", "http://localhost:5000")
            # 获取agent区域信息
            agent_area = self.config.get("agent_area", "default_area")
            
            # 在请求中添加区域参数
            response = requests.get(f"{server_url}/api/v1/tasks?enabled=true&area={agent_area}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0:
                    # 转换后端任务格式为agent可识别的格式
                    self.tasks = []
                    for task in data.get("data", {}).get("list", []):
                        # 将后端任务格式转换为agent内部格式
                        converted_task = {
                            "task_id": task["id"],
                            "type": task["type"],
                            "target": task["target"],  # 获取目标地址
                            "interval": task["interval"],  # 获取时间间隔
                            "params": json.loads(task["config"]) if task["config"] else {
                                "count": 4  # 默认ping次数
                            }
                        }
                        self.tasks.append(converted_task)
                    
                    logger.info(f"从服务器获取到 {len(self.tasks)} 个拨测任务")
                    return self.tasks
                else:
                    logger.error(f"获取任务失败: {data.get('message')}")
            else:
                logger.error(f"获取任务HTTP错误: {response.status_code}")
        except Exception as e:
            logger.error(f"获取任务时发生异常: {e}")
        
        # 如果无法从服务器获取任务，则返回空列表
        self.tasks = []
        return self.tasks
    
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行单个拨测任务
        
        Args:
            task: 任务配置
            
        Returns:
            任务执行结果
        """
        task_type = task.get("type")
        task_id = task.get("task_id")
        
        if task_type not in self.plugins:
            logger.error(f"未找到任务类型对应的插件: {task_type}")
            return {
                "task_id": task_id,
                "status": "error",
                "message": f"插件 {task_type} 未找到"
            }
        
        try:
            # 执行插件
            plugin = self.plugins[task_type]
            result = plugin.execute(task)
            
            # 记录任务详细输出（按error级别输出）
            logger.error(f"任务 {task_id} 详细输出: {json.dumps(result, ensure_ascii=False)}")
            
            logger.info(f"任务 {task_id} 执行完成")
            return {
                "task_id": task_id,
                "status": "success",
                "result": result,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"执行任务 {task_id} 失败: {e}")
            return {
                "task_id": task_id,
                "status": "error",
                "message": str(e),
                "timestamp": time.time()
            }
    
    def report_result(self, result: Dict[str, Any]) -> None:
        """
        上报任务执行结果到后端服务器
        
        Args:
            result: 任务执行结果
        """
        try:
            server_url = self.config.get("server_url", "http://localhost:5000")
            
            # 获取本地时间并格式化为ISO格式
            local_time = datetime.fromtimestamp(time.time()).isoformat()
            
            # 获取agent区域信息
            agent_area = self.config.get("agent_area", "default_area")
            
            response = requests.post(
                f"{server_url}/api/v1/results",
                headers={"Content-Type": "application/json"},
                json={
                    "task_id": result["task_id"],
                    "status": result["status"],
                    "response_time": result.get("result", {}).get("execution_time"),
                    "message": result.get("message", ""),
                    "details": result.get("result", {}),
                    "created_at": local_time,  # 使用本地时间
                    "agent_area": agent_area   # 添加区域信息
                }
            )
            
            if response.status_code == 201:
                logger.info(f"任务结果上报成功: task_id={result['task_id']}")
            else:
                logger.error(f"任务结果上报失败: status_code={response.status_code}, response={response.text}")
        except Exception as e:
            logger.error(f"上报任务结果时发生异常: {e}")
    
    def run_tasks(self) -> None:
        """执行所有拨测任务"""
        if not self.tasks:
            self.get_tasks()
        
        for task in self.tasks:
            result = self.execute_task(task)
            self.report_result(result)
    
    def run(self) -> None:
        """运行Agent主循环"""
        # 注册agent
        if not self.register_agent():
            logger.error("Agent注册失败，退出")
            return
        
        # 启动心跳线程
        self.start_heartbeat()
        
        logger.info("拨测Agent启动")
        
        # 用于跟踪每个任务的下次执行时间
        next_execution_times = {}
        current_time = time.time()
        
        # 初始化下次执行时间
        for task in self.get_tasks():
            next_execution_times[task["task_id"]] = current_time
        
        while self.running:
            try:
                current_time = time.time()
                
                # 获取最新任务列表
                self.get_tasks()
                
                # 执行到达执行时间的任务
                for task in self.tasks:
                    task_id = task["task_id"]
                    interval = task["interval"]
                    
                    # 初始化任务的下次执行时间
                    if task_id not in next_execution_times:
                        next_execution_times[task_id] = current_time
                    
                    # 检查是否到达执行时间
                    if current_time >= next_execution_times[task_id]:
                        # 执行任务
                        result = self.execute_task(task)
                        self.report_result(result)
                        
                        # 更新下次执行时间
                        next_execution_times[task_id] = current_time + interval
                        logger.info(f"任务 {task_id} 将在 {interval} 秒后再次执行")
                
                # 等待一段时间再检查
                time.sleep(5)  # 每5秒检查一次任务是否需要执行
                
            except KeyboardInterrupt:
                logger.info("收到退出信号，正在停止Agent")
                break
            except Exception as e:
                logger.error(f"执行过程中发生错误: {e}")
                time.sleep(10)  # 出错后等待10秒再重试
        
        # 停止心跳线程
        self.stop_heartbeat()
    
    def stop(self):
        """停止Agent"""
        self.running = False


def main():
    """主函数"""
    agent = DialerAgent()
    
    try:
        agent.run()
    except KeyboardInterrupt:
        logger.info("收到退出信号，正在停止Agent")
        agent.stop()


if __name__ == "__main__":
    main()