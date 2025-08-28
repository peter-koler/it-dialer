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
            
            # 准备请求头
            headers = {"Content-Type": "application/json"}
            
            # 如果启用认证，添加认证头
            if self.config.get("auth_required", False):
                api_token = self.config.get("api_token", "")
                if api_token:
                    headers["Authorization"] = f"Bearer {api_token}"
                else:
                    logger.warning("认证已启用但未配置API token")
            
            # 准备Agent数据
            agent_data = self.agent_info.copy()
            
            response = requests.post(
                f"{server_url}/api/v1/nodes/register",
                headers=headers,
                json=agent_data
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
    
    def update_agent_info(self):
        """更新agent信息"""
        try:
            server_url = self.config.get("server_url", "http://localhost:5000")
            
            # 准备请求头
            headers = {"Content-Type": "application/json"}
            
            # 如果启用认证，添加认证头
            if self.config.get("auth_required", False):
                api_token = self.config.get("api_token", "")
                if api_token:
                    headers["Authorization"] = f"Bearer {api_token}"
                else:
                    logger.warning("认证已启用但未配置API token")
            
            # 准备Agent数据
            agent_data = self.agent_info.copy()
            
            response = requests.post(
                f"{server_url}/api/v1/nodes/register",
                headers=headers,
                json=agent_data
            )
            
            if response.status_code == 200 or response.status_code == 201:
                logger.info("Agent信息更新成功")
                return True
            else:
                logger.error(f"Agent信息更新失败: status_code={response.status_code}, response={response.text}")
                return False
        except Exception as e:
            logger.error(f"Agent信息更新时发生异常: {e}")
            return False
    
    def send_heartbeat(self):
        """发送心跳信息到服务器"""
        try:
            server_url = self.config.get("server_url", "http://localhost:5000")
            
            # 准备请求头
            headers = {"Content-Type": "application/json"}
            
            # 如果启用认证，添加认证头
            if self.config.get("auth_required", False):
                api_token = self.config.get("api_token", "")
                if api_token:
                    headers["Authorization"] = f"Bearer {api_token}"
                else:
                    logger.warning("认证已启用但未配置API token")
            
            # 准备心跳数据
            heartbeat_data = {
                "agent_id": self.agent_info["agent_id"],
                "timestamp": datetime.fromtimestamp(time.time()).isoformat()
            }
            
            response = requests.post(
                f"{server_url}/api/v1/nodes/heartbeat",
                headers=headers,
                json=heartbeat_data
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
            # 获取agent信息
            agent_id = self.config.get("agent_id", "default_agent")
            
            # 准备请求头
            headers = {"Content-Type": "application/json"}
            
            # 如果启用认证，添加认证头
            if self.config.get("auth_required", False):
                api_token = self.config.get("api_token", "")
                if api_token:
                    headers["Authorization"] = f"Bearer {api_token}"
                else:
                    logger.warning("认证已启用但未配置API token")
            
            # 在请求中添加agent_id参数，只获取分配给当前agent的任务
            response = requests.get(
                f"{server_url}/api/v1/tasks/agent?enabled=true&agent_id={agent_id}",
                headers=headers
            )
            
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
                            "tenant_id": task.get("tenant_id"),  # 保存租户ID
                            "params": {}
                        }
                        
                        # 安全地处理config字段
                        config_data = task.get("config")
                        if config_data:
                            try:
                                # 如果config_data已经是dict类型，直接使用
                                if isinstance(config_data, dict):
                                    converted_task["config"] = config_data
                                # 如果config_data是字符串，尝试解析为JSON
                                elif isinstance(config_data, str):
                                    converted_task["config"] = json.loads(config_data)
                                else:
                                    logger.warning(f"任务 {task['id']} 的config字段类型未知: {type(config_data)}")
                                    converted_task["config"] = {"count": 4}  # 默认ping次数
                            except (json.JSONDecodeError, TypeError) as e:
                                logger.warning(f"任务 {task['id']} 的config字段解析失败: {e}")
                                converted_task["config"] = {"count": 4}  # 默认ping次数
                        else:
                            # 根据任务类型设置默认配置
                            if task.get("type") == "ping":
                                converted_task["config"] = {"count": 4}  # 默认ping次数
                            elif task.get("type") == "api":
                                converted_task["config"] = {"steps": []}  # API任务默认配置
                            else:
                                converted_task["config"] = {}
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
        # 类型检查
        if not isinstance(task, dict):
            logger.error(f"任务参数类型错误，期望dict，实际得到{type(task)}")
            return {
                "task_id": "unknown",
                "status": "error",
                "message": f"任务参数类型错误: {type(task)}"
            }
            
        task_type = task.get("type")
        task_id = task.get("task_id")
        
        # 确保params字段存在且为字典类型
        if "params" not in task or not isinstance(task.get("params"), dict):
            task["params"] = {}
            
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
            logger.info(f"执行任务 {task_id}, 类型: {task_type}, 完整任务: {json.dumps(task, ensure_ascii=False)}")
            result = plugin.execute(task)
            
            # 记录任务详细输出（按error级别输出）
            logger.error(f"任务 {task_id} 详细输出: {json.dumps(result, ensure_ascii=False)}")
            
            # 获取插件执行的实际状态
            plugin_status = result.get("status", "success")
            plugin_message = result.get("message", "")
            
            logger.info(f"任务 {task_id} 执行完成")
            return {
                "task_id": task_id,
                "status": plugin_status,  # 使用插件返回的实际状态
                "result": result,
                "message": plugin_message,  # 添加插件返回的消息
                "tenant_id": task.get("tenant_id"),  # 传递租户ID
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"执行任务 {task_id} 失败: {e}")
            return {
                "task_id": task_id,
                "status": "error",
                "message": str(e),
                "tenant_id": task.get("tenant_id"),  # 传递租户ID
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
            
            # 获取agent信息
            agent_id = self.config.get("agent_id", "default_agent")
            agent_area = self.config.get("agent_area", "default_area")
            
            # 准备请求头
            headers = {"Content-Type": "application/json"}
            
            # 如果启用认证，添加认证头
            if self.config.get("auth_required", False):
                api_token = self.config.get("api_token", "")
                if api_token:
                    headers["Authorization"] = f"Bearer {api_token}"
                else:
                    logger.warning("认证已启用但未配置API token")
            
            # 准备上报数据
            report_data = {
                "task_id": result["task_id"],
                "status": result["status"],
                "response_time": result.get("result", {}).get("execution_time"),
                "message": result.get("message", ""),
                "details": result.get("result", {}),
                "created_at": local_time,  # 使用本地时间
                "agent_id": agent_id,      # 添加agent_id信息
                "agent_area": agent_area,  # 添加区域信息
                "tenant_id": result.get("tenant_id")  # 添加租户ID
            }
            
            response = requests.post(
                f"{server_url}/api/v1/results",
                headers=headers,
                json=report_data
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
        # 设置环境变量SERVER_URL供插件使用
        os.environ["SERVER_URL"] = self.config.get("server_url", "http://localhost:5000")
        
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
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # 创建Agent实例
        agent = DialerAgent()
        
        # 设置环境变量SERVER_URL供插件使用
        os.environ["SERVER_URL"] = agent.config.get("server_url", "http://localhost:5000")
        
        # 注册agent到服务器
        if not agent.register_agent():
            logger.error("Agent注册失败，退出程序")
            return
            
        # 更新agent信息（确保数据库中的信息是最新的）
        agent.update_agent_info()
        
        # 启动心跳线程
        agent.start_heartbeat()
        
        # 主循环
        while True:
            try:
                # 获取任务
                tasks = agent.get_tasks()
                
                # 执行任务
                for task in tasks:
                    result = agent.execute_task(task)
                    agent.report_result(result)
                
                # 等待下次执行
                interval = agent.config.get("report_interval", 60)
                logger.info(f"任务执行完成，将在 {interval} 秒后再次执行")
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("收到退出信号")
                break
            except Exception as e:
                logger.error(f"执行任务时发生异常: {e}")
                time.sleep(10)  # 出错时等待10秒再继续
                
    except Exception as e:
        logger.error(f"Agent运行时发生异常: {e}")
    finally:
        # 停止心跳线程
        if 'agent' in locals():
            agent.stop_heartbeat()
        logger.info("拨测Agent已停止")


if __name__ == "__main__":
    main()