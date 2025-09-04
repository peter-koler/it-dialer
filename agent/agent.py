#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
拨测Agent主模块 - 混合模式版本
功能：支持插件加载，基于线程池的任务调度和执行
"""

import os
import sys
import json
import importlib
import time
import requests
import socket
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
from threading import Thread

# 导入自定义模块
from scheduler import TaskScheduler
from logger import setup_agent_logging, ThreadSafeLogger


class DialerAgent:
    """拨测Agent类 - 混合模式版本"""
    
    def __init__(self, config_path: str = "agent_config.json"):
        """
        初始化拨测Agent
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = {}
        self.plugins = {}
        self.agent_info = {}
        
        # 加载配置
        self.load_config()
        
        # 设置日志系统
        self.logger = setup_agent_logging(self.config.get('logging', {}))
        self.logger.info("Agent初始化开始")
        
        # 获取agent信息
        self.collect_agent_info()
        
        # 加载插件
        self.load_plugins()
        
        # 初始化任务调度器
        thread_pool_config = self.config.get('thread_pool', {})
        max_workers = thread_pool_config.get('max_workers', 10)
        self.scheduler = TaskScheduler(max_workers=max_workers, logger=self.logger)
        
        # 心跳线程
        self.heartbeat_thread = None
        self.running = False
        
        # 任务同步间隔
        self.task_sync_interval = 30  # 30秒同步一次任务
        self.last_task_sync_time = 0
        
        self.logger.info(f"Agent初始化完成 - 最大线程数: {max_workers}")
    
    def collect_agent_info(self):
        """收集agent信息"""
        self.agent_info = {
            "agent_id": self.config.get("agent_id", "default_agent"),
            "agent_area": self.config.get("agent_area", "default_area"),
            "ip_address": self.get_local_ip(),
            "hostname": socket.gethostname()
        }
        self.logger.info(f"Agent信息: {self.agent_info}")
    
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
            self.logger.error(f"获取本机IP失败: {e}")
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
                    "server_url": "http://localhost:5001",
                    "plugins_dir": "plugins",
                    "report_interval": 60,
                    "log_level": "INFO",
                    "agent_area": "default_area",
                    "thread_pool": {
                        "max_workers": 10,
                        "task_timeout": 300,
                        "queue_size_limit": 100
                    },
                    "logging": {
                        "log_mode": "INFO",
                        "log_path": "logs",
                        "log_name": "agent",
                        "log_rotation": True
                    }
                }
                self.save_config()
                
            print("配置加载成功")
        except Exception as e:
            print(f"加载配置失败: {e}")
            raise
    
    def save_config(self) -> None:
        """保存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            self.logger.info("配置保存成功")
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
    
    def load_plugins(self) -> None:
        """加载插件"""
        plugins_dir = self.config.get("plugins_dir", "plugins")
        
        # 确保插件目录存在
        if not os.path.exists(plugins_dir):
            os.makedirs(plugins_dir)
            self.logger.info(f"创建插件目录: {plugins_dir}")
        
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
                    self.logger.info(f"插件加载成功: {module.PLUGIN_NAME}")
                else:
                    self.logger.warning(f"插件 {module_name} 缺少必要属性，跳过加载")
                    
            except Exception as e:
                self.logger.error(f"加载插件 {plugin_file.name} 失败: {e}")
        
        self.logger.info(f"插件加载完成，共加载 {len(self.plugins)} 个插件")
    
    def register_agent(self):
        """注册agent到服务器"""
        try:
            server_url = self.config.get("server_url", "http://localhost:5001")
            
            # 准备请求头
            headers = {"Content-Type": "application/json"}
            
            # 如果启用认证，添加认证头
            if self.config.get("auth_required", False):
                api_token = self.config.get("api_token", "")
                if api_token:
                    headers["Authorization"] = f"Bearer {api_token}"
                else:
                    self.logger.warning("认证已启用但未配置API token")
            
            # 准备Agent数据
            agent_data = self.agent_info.copy()
            
            response = requests.post(
                f"{server_url}/api/v1/nodes/register",
                headers=headers,
                json=agent_data
            )
            
            if response.status_code == 200 or response.status_code == 201:
                self.logger.info("Agent注册成功")
                return True
            else:
                self.logger.error(f"Agent注册失败: status_code={response.status_code}, response={response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Agent注册时发生异常: {e}")
            return False
    
    def send_heartbeat(self):
        """发送心跳信息到服务器"""
        try:
            server_url = self.config.get("server_url", "http://localhost:5001")
            
            # 准备请求头
            headers = {"Content-Type": "application/json"}
            
            # 如果启用认证，添加认证头
            if self.config.get("auth_required", False):
                api_token = self.config.get("api_token", "")
                if api_token:
                    headers["Authorization"] = f"Bearer {api_token}"
                else:
                    self.logger.warning("认证已启用但未配置API token")
            
            # 获取线程池状态
            thread_pool_status = self.scheduler.get_thread_pool_status()
            task_status = self.scheduler.get_task_status()
            
            # 准备心跳数据
            heartbeat_data = {
                "agent_id": self.agent_info["agent_id"],
                "timestamp": datetime.fromtimestamp(time.time()).isoformat(),
                "thread_pool": {
                    "max_workers": thread_pool_status["max_workers"],
                    "active_threads": thread_pool_status["active_threads"],
                    "completed_tasks": thread_pool_status["completed_tasks"],
                    "pending_tasks": thread_pool_status["pending_tasks"]
                },
                "task_status": {
                    "total_tasks": task_status["total_tasks"],
                    "running_tasks": task_status["running_tasks"],
                    "pending_tasks": task_status["pending_tasks"],
                    "completed_tasks": task_status["completed_tasks"],
                    "failed_tasks": task_status["failed_tasks"]
                }
            }
            
            response = requests.post(
                f"{server_url}/api/v1/nodes/heartbeat",
                headers=headers,
                json=heartbeat_data
            )
            
            if response.status_code == 200:
                self.logger.info("心跳信息发送成功")
                # 记录线程池状态
                self.logger.log_thread_pool_status(**thread_pool_status)
                return True
            else:
                self.logger.error(f"心跳信息发送失败: status_code={response.status_code}, response={response.text}")
                return False
        except Exception as e:
            self.logger.error(f"发送心跳信息时发生异常: {e}")
            return False
    
    def heartbeat_worker(self):
        """心跳工作线程"""
        heartbeat_interval = self.config.get('heartbeat_interval', 30)
        while self.running:
            self.send_heartbeat()
            # 根据配置文件设置心跳间隔
            time.sleep(heartbeat_interval)
    
    def start_heartbeat(self):
        """启动心跳线程"""
        self.running = True
        self.heartbeat_thread = Thread(target=self.heartbeat_worker, name="HeartbeatWorker")
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()
        self.logger.info("心跳线程已启动")
    
    def stop_heartbeat(self):
        """停止心跳线程"""
        self.running = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join()
        self.logger.info("心跳线程已停止")
    
    def get_tasks_from_server(self) -> List[Dict[str, Any]]:
        """
        从服务器获取任务列表
        
        Returns:
            任务列表
        """
        try:
            server_url = self.config.get("server_url", "http://localhost:5001")
            agent_id = self.config.get("agent_id", "default_agent")
            
            # 准备请求头
            headers = {"Content-Type": "application/json"}
            
            # 如果启用认证，添加认证头
            if self.config.get("auth_required", False):
                api_token = self.config.get("api_token", "")
                if api_token:
                    headers["Authorization"] = f"Bearer {api_token}"
                else:
                    self.logger.warning("认证已启用但未配置API token")
            
            # 在请求中添加agent_id参数，只获取分配给当前agent的任务
            response = requests.get(
                f"{server_url}/api/v1/tasks/agent?enabled=true&agent_id={agent_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0:
                    # 转换后端任务格式为调度器可识别的格式
                    tasks = []
                    for task in data.get("data", {}).get("list", []):
                        # 将后端任务格式转换为调度器内部格式
                        converted_task = {
                            "task_id": str(task["id"]),
                            "type": task["type"],
                            "target": task["target"],
                            "interval": task["interval"],
                            "tenant_id": task.get("tenant_id"),
                            "params": {}
                        }
                        
                        # 安全地处理config字段
                        config_data = task.get("config")
                        if config_data:
                            try:
                                if isinstance(config_data, dict):
                                    converted_task["config"] = config_data
                                elif isinstance(config_data, str):
                                    converted_task["config"] = json.loads(config_data)
                                else:
                                    self.logger.warning(f"任务 {task['id']} 的config字段类型未知: {type(config_data)}")
                                    converted_task["config"] = self._get_default_config(task.get("type"))
                            except (json.JSONDecodeError, TypeError) as e:
                                self.logger.warning(f"任务 {task['id']} 的config字段解析失败: {e}")
                                converted_task["config"] = self._get_default_config(task.get("type"))
                        else:
                            converted_task["config"] = self._get_default_config(task.get("type"))
                        
                        tasks.append(converted_task)
                    
                    self.logger.debug(f"从服务器获取到 {len(tasks)} 个任务")
                    return tasks
                else:
                    self.logger.error(f"获取任务失败: {data.get('message')}")
            else:
                self.logger.error(f"获取任务HTTP错误: {response.status_code}")
        except Exception as e:
            self.logger.error(f"获取任务时发生异常: {e}")
        
        return []
    
    def _get_default_config(self, task_type: str) -> Dict[str, Any]:
        """获取任务类型的默认配置"""
        default_configs = {
            "ping": {"count": 4},
            "api": {"steps": []},
            "tcp": {"timeout": 10},
            "http": {"timeout": 30}
        }
        return default_configs.get(task_type, {})
    
    def execute_task(self, task: Dict[str, Any], plugins: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行单个拨测任务
        
        Args:
            task: 任务配置
            plugins: 插件字典
            
        Returns:
            任务执行结果
        """
        # 类型检查
        if not isinstance(task, dict):
            self.logger.error(f"任务参数类型错误，期望dict，实际得到{type(task)}")
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
            
        if task_type not in plugins:
            self.logger.error(f"未找到任务类型对应的插件: {task_type}")
            return {
                "task_id": task_id,
                "status": "error",
                "message": f"插件 {task_type} 未找到"
            }
        
        try:
            # 执行插件
            plugin = plugins[task_type]
            self.logger.debug(f"执行任务 {task_id}, 类型: {task_type}")
            result = plugin.execute(task)
            
            # 获取插件执行的实际状态
            plugin_status = result.get("status", "success")
            plugin_message = result.get("message", "")
            
            self.logger.debug(f"任务 {task_id} 执行完成")
            return {
                "task_id": task_id,
                "status": plugin_status,
                "result": result,
                "message": plugin_message,
                "tenant_id": task.get("tenant_id"),
                "timestamp": time.time()
            }
        except Exception as e:
            self.logger.error(f"执行任务 {task_id} 失败: {e}")
            return {
                "task_id": task_id,
                "status": "error",
                "message": str(e),
                "tenant_id": task.get("tenant_id"),
                "timestamp": time.time()
            }
    
    def report_result(self, result: Dict[str, Any]) -> None:
        """
        上报任务执行结果到后端服务器
        
        Args:
            result: 任务执行结果
        """
        try:
            server_url = self.config.get("server_url", "http://localhost:5001")
            
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
                    self.logger.warning("认证已启用但未配置API token")
            
            # 准备上报数据
            report_data = {
                "task_id": result["task_id"],
                "status": result["status"],
                "response_time": result.get("result", {}).get("execution_time"),
                "message": result.get("message", ""),
                "details": result.get("result", {}),
                "created_at": local_time,
                "agent_id": agent_id,
                "agent_area": agent_area,
                "tenant_id": result.get("tenant_id")
            }
            
            response = requests.post(
                f"{server_url}/api/v1/results",
                headers=headers,
                json=report_data
            )
            
            if response.status_code == 201:
                self.logger.debug(f"任务结果上报成功: task_id={result['task_id']}")
            else:
                self.logger.error(f"任务结果上报失败: status_code={response.status_code}, response={response.text}")
        except Exception as e:
            self.logger.error(f"上报任务结果时发生异常: {e}")
    
    def sync_tasks_with_server(self):
        """与服务器同步任务列表"""
        current_time = time.time()
        if current_time - self.last_task_sync_time < self.task_sync_interval:
            return
        
        try:
            # 获取服务器任务列表
            server_tasks = self.get_tasks_from_server()
            
            # 同步任务到调度器
            sync_stats = self.scheduler.sync_tasks(server_tasks)
            
            # 记录同步结果
            if sum(sync_stats.values()) > 0:
                self.logger.info(f"任务同步完成: 新增{sync_stats['added']}个, 更新{sync_stats['updated']}个, 删除{sync_stats['removed']}个")
            
            self.last_task_sync_time = current_time
            
        except Exception as e:
            self.logger.error(f"同步任务时发生异常: {e}")
    
    def run(self) -> None:
        """运行Agent主循环"""
        # 设置环境变量SERVER_URL供插件使用
        os.environ["SERVER_URL"] = self.config.get("server_url", "http://localhost:5001")
        
        # 注册agent
        if not self.register_agent():
            self.logger.error("Agent注册失败，退出")
            return
        
        # 启动心跳线程
        self.start_heartbeat()
        
        # 启动任务调度器
        self.scheduler.start(
            execute_func=self.execute_task,
            plugins=self.plugins,
            report_func=self.report_result
        )
        
        self.logger.info("拨测Agent启动完成 - 混合模式")
        
        try:
            while self.running:
                # 定期同步任务
                self.sync_tasks_with_server()
                
                # 等待一段时间再检查
                time.sleep(10)
                
        except KeyboardInterrupt:
            self.logger.info("收到退出信号，正在停止Agent")
        except Exception as e:
            self.logger.error(f"Agent运行过程中发生错误: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """停止Agent"""
        self.logger.info("正在停止Agent...")
        self.running = False
        
        # 停止任务调度器
        if hasattr(self, 'scheduler'):
            self.scheduler.stop()
        
        # 停止心跳线程
        self.stop_heartbeat()
        
        self.logger.info("Agent已停止")


def main():
    """主函数"""
    try:
        # 创建Agent实例
        agent = DialerAgent()
        
        # 设置环境变量SERVER_URL供插件使用
        os.environ["SERVER_URL"] = agent.config.get("server_url", "http://localhost:5001")
        
        # 运行Agent
        agent.run()
        
    except Exception as e:
        print(f"Agent运行时发生异常: {e}")
    finally:
        print("拨测Agent已停止")


if __name__ == "__main__":
    main()