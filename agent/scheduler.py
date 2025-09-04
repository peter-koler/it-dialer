#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
任务调度器模块
实现基于线程池的任务调度和管理
"""

import time
import threading
import logging
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class TaskInfo:
    """任务信息数据类"""
    task_id: str
    tenant_id: str
    task_type: str
    target: str
    interval: int
    config: Dict[str, Any]
    next_execution_time: float
    is_running: bool = False
    last_execution_time: Optional[float] = None
    execution_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "task_id": self.task_id,
            "tenant_id": self.tenant_id,
            "type": self.task_type,
            "target": self.target,
            "interval": self.interval,
            "config": self.config,
            "next_execution_time": self.next_execution_time,
            "is_running": self.is_running,
            "last_execution_time": self.last_execution_time,
            "execution_count": self.execution_count
        }


class TaskScheduler:
    """任务调度器类"""
    
    def __init__(self, max_workers: int = 10, logger: Optional[logging.Logger] = None):
        """
        初始化任务调度器
        
        Args:
            max_workers: 线程池最大工作线程数
            logger: 日志记录器
        """
        self.max_workers = max_workers
        self.logger = logger or logging.getLogger(__name__)
        
        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="TaskWorker")
        
        # 任务管理
        self.tasks: Dict[str, TaskInfo] = {}  # task_id -> TaskInfo
        self.running_futures: Dict[str, Future] = {}  # task_id -> Future
        
        # 线程安全锁
        self.lock = threading.RLock()
        
        # 调度器状态
        self.is_running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        
        # 统计信息
        self.total_completed_tasks = 0
        self.total_failed_tasks = 0
        
        self.logger.info(f"任务调度器初始化完成，最大线程数: {max_workers}")
    
    def add_task(self, task_data: Dict[str, Any]) -> bool:
        """
        添加任务到调度器
        
        Args:
            task_data: 任务数据字典
            
        Returns:
            是否添加成功
        """
        try:
            task_id = task_data.get("task_id")
            if not task_id:
                self.logger.error("任务缺少task_id字段")
                return False
            
            with self.lock:
                # 检查任务是否已存在
                if task_id in self.tasks:
                    self.logger.warning(f"任务 {task_id} 已存在，将更新任务配置")
                    return self.update_task(task_data)
                
                # 检查任务数量是否超过线程池最大配置
                current_task_count = len(self.tasks)
                if current_task_count >= self.max_workers:
                    self.logger.warning(f"任务数量 ({current_task_count}) 已达到线程池最大配置 ({self.max_workers})，新增任务可能影响性能")
                    self.logger.warning(f"建议增加线程池配置 max_workers 或减少任务数量")
                
                # 创建任务信息
                task_info = TaskInfo(
                    task_id=task_id,
                    tenant_id=task_data.get("tenant_id", ""),
                    task_type=task_data.get("type", ""),
                    target=task_data.get("target", ""),
                    interval=task_data.get("interval", 60),
                    config=task_data.get("config", {}),
                    next_execution_time=time.time()  # 立即执行
                )
                
                self.tasks[task_id] = task_info
                self.logger.info(f"新增任务 task_id={task_id}, interval={task_info.interval}s, tenant={task_info.tenant_id}")
                self.logger.info(f"当前任务总数: {len(self.tasks)}/{self.max_workers}")
                return True
                
        except Exception as e:
            self.logger.error(f"添加任务失败: {e}")
            return False
    
    def update_task(self, task_data: Dict[str, Any]) -> bool:
        """
        更新任务配置
        
        Args:
            task_data: 新的任务数据
            
        Returns:
            是否更新成功
        """
        try:
            task_id = task_data.get("task_id")
            if not task_id:
                return False
            
            with self.lock:
                if task_id not in self.tasks:
                    self.logger.warning(f"任务 {task_id} 不存在，无法更新")
                    return False
                
                task_info = self.tasks[task_id]
                old_interval = task_info.interval
                
                # 更新任务信息
                task_info.tenant_id = task_data.get("tenant_id", task_info.tenant_id)
                task_info.task_type = task_data.get("type", task_info.task_type)
                task_info.target = task_data.get("target", task_info.target)
                task_info.interval = task_data.get("interval", task_info.interval)
                task_info.config = task_data.get("config", task_info.config)
                
                # 如果间隔时间改变，重新计算下次执行时间
                if old_interval != task_info.interval:
                    task_info.next_execution_time = time.time() + task_info.interval
                
                self.logger.info(f"修改任务 task_id={task_id}, 新间隔={task_info.interval}s")
                return True
                
        except Exception as e:
            self.logger.error(f"更新任务失败: {e}")
            return False
    
    def remove_task(self, task_id: str) -> bool:
        """
        删除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否删除成功
        """
        try:
            with self.lock:
                if task_id not in self.tasks:
                    self.logger.warning(f"任务 {task_id} 不存在，无法删除")
                    return False
                
                # 如果任务正在运行，尝试取消
                if task_id in self.running_futures:
                    future = self.running_futures[task_id]
                    if not future.done():
                        future.cancel()
                        self.logger.info(f"已取消正在运行的任务 {task_id}")
                    del self.running_futures[task_id]
                
                # 删除任务
                del self.tasks[task_id]
                self.logger.info(f"删除任务 task_id={task_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"删除任务失败: {e}")
            return False
    
    def get_task_status(self) -> Dict[str, Any]:
        """
        获取任务状态信息
        
        Returns:
            任务状态字典
        """
        with self.lock:
            running_tasks = sum(1 for task in self.tasks.values() if task.is_running)
            pending_tasks = len(self.tasks) - running_tasks
            
            return {
                "total_tasks": len(self.tasks),
                "running_tasks": running_tasks,
                "pending_tasks": pending_tasks,
                "completed_tasks": self.total_completed_tasks,
                "failed_tasks": self.total_failed_tasks
            }
    
    def get_thread_pool_status(self) -> Dict[str, Any]:
        """
        获取线程池状态信息
        
        Returns:
            线程池状态字典
        """
        # 获取活跃线程数
        active_threads = 0
        if hasattr(self.executor, '_threads'):
            active_threads = len([t for t in self.executor._threads if t.is_alive()])
        
        return {
            "max_workers": self.max_workers,
            "active_threads": active_threads,
            "completed_tasks": self.total_completed_tasks,
            "pending_tasks": len(self.running_futures)
        }
    
    def _execute_task_wrapper(self, task_info: TaskInfo, execute_func, plugins: Dict[str, Any]) -> Dict[str, Any]:
        """
        任务执行包装器
        
        Args:
            task_info: 任务信息
            execute_func: 任务执行函数
            plugins: 插件字典
            
        Returns:
            任务执行结果
        """
        task_id = task_info.task_id
        
        try:
            # 标记任务开始执行
            with self.lock:
                task_info.is_running = True
                task_info.last_execution_time = time.time()
                task_info.execution_count += 1
            
            self.logger.debug(f"开始执行任务 {task_id}")
            
            # 执行任务
            result = execute_func(task_info.to_dict(), plugins)
            
            # 更新统计信息
            with self.lock:
                if result.get("status") == "error":
                    self.total_failed_tasks += 1
                    self.logger.error(f"任务执行失败 task_id={task_id}, error={result.get('message')}")
                else:
                    self.total_completed_tasks += 1
            
            self.logger.debug(f"任务 {task_id} 执行完成")
            return result
            
        except Exception as e:
            with self.lock:
                self.total_failed_tasks += 1
            
            error_msg = str(e)
            self.logger.error(f"任务执行失败 task_id={task_id}, error={error_msg}")
            return {
                "task_id": task_id,
                "status": "error",
                "message": error_msg,
                "tenant_id": task_info.tenant_id,
                "timestamp": time.time()
            }
        finally:
            # 标记任务执行完成
            with self.lock:
                task_info.is_running = False
                # 计算下次执行时间
                task_info.next_execution_time = time.time() + task_info.interval
                # 清理运行中的Future
                if task_id in self.running_futures:
                    del self.running_futures[task_id]
    
    def _scheduler_loop(self, execute_func, plugins: Dict[str, Any], report_func):
        """
        调度器主循环
        
        Args:
            execute_func: 任务执行函数
            plugins: 插件字典
            report_func: 结果上报函数
        """
        self.logger.info("任务调度器开始运行")
        
        while self.is_running:
            try:
                current_time = time.time()
                tasks_to_execute = []
                
                # 查找需要执行的任务
                with self.lock:
                    for task_info in self.tasks.values():
                        if (not task_info.is_running and 
                            current_time >= task_info.next_execution_time):
                            tasks_to_execute.append(task_info)
                
                # 提交任务到线程池
                for task_info in tasks_to_execute:
                    try:
                        future = self.executor.submit(
                            self._execute_task_wrapper,
                            task_info,
                            execute_func,
                            plugins
                        )
                        
                        # 添加回调函数处理结果
                        future.add_done_callback(
                            lambda f, tid=task_info.task_id: self._handle_task_result(f, tid, report_func)
                        )
                        
                        with self.lock:
                            self.running_futures[task_info.task_id] = future
                        
                        self.logger.debug(f"任务 {task_info.task_id} 已提交到线程池")
                        
                    except Exception as e:
                        self.logger.error(f"提交任务 {task_info.task_id} 到线程池失败: {e}")
                
                # 记录线程池状态
                if len(tasks_to_execute) > 0:
                    pool_status = self.get_thread_pool_status()
                    self.logger.debug(f"当前线程池 active={pool_status['active_threads']}, pending={pool_status['pending_tasks']}, completed={pool_status['completed_tasks']}")
                
                # 等待一段时间再检查
                time.sleep(5)
                
            except Exception as e:
                self.logger.error(f"调度器循环发生异常: {e}")
                time.sleep(10)
        
        self.logger.info("任务调度器已停止")
    
    def _handle_task_result(self, future: Future, task_id: str, report_func):
        """
        处理任务执行结果
        
        Args:
            future: 任务执行的Future对象
            task_id: 任务ID
            report_func: 结果上报函数
        """
        try:
            result = future.result()
            if report_func:
                report_func(result)
        except Exception as e:
            self.logger.error(f"处理任务 {task_id} 结果时发生异常: {e}")
    
    def start(self, execute_func, plugins: Dict[str, Any], report_func):
        """
        启动任务调度器
        
        Args:
            execute_func: 任务执行函数
            plugins: 插件字典
            report_func: 结果上报函数
        """
        if self.is_running:
            self.logger.warning("任务调度器已在运行中")
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            args=(execute_func, plugins, report_func),
            name="TaskScheduler"
        )
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        self.logger.info("任务调度器已启动")
    
    def stop(self):
        """
        停止任务调度器
        """
        if not self.is_running:
            return
        
        self.logger.info("正在停止任务调度器...")
        self.is_running = False
        
        # 等待调度器线程结束
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=10)
        
        # 取消所有正在运行的任务
        with self.lock:
            for future in self.running_futures.values():
                if not future.done():
                    future.cancel()
        
        # 关闭线程池
        self.executor.shutdown(wait=True)
        
        self.logger.info("任务调度器已停止")
    
    def sync_tasks(self, new_tasks: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        同步任务列表（处理任务的增删改）
        
        Args:
            new_tasks: 新的任务列表
            
        Returns:
            同步结果统计 {"added": 0, "updated": 0, "removed": 0}
        """
        stats = {"added": 0, "updated": 0, "removed": 0}
        
        try:
            new_task_ids = {task.get("task_id") for task in new_tasks if task.get("task_id")}
            current_task_ids = set(self.tasks.keys())
            
            # 处理新增和更新的任务
            for task_data in new_tasks:
                task_id = task_data.get("task_id")
                if not task_id:
                    continue
                
                if task_id in current_task_ids:
                    # 更新现有任务
                    if self.update_task(task_data):
                        stats["updated"] += 1
                else:
                    # 添加新任务
                    if self.add_task(task_data):
                        stats["added"] += 1
            
            # 处理需要删除的任务
            tasks_to_remove = current_task_ids - new_task_ids
            for task_id in tasks_to_remove:
                if self.remove_task(task_id):
                    stats["removed"] += 1
            
            if sum(stats.values()) > 0:
                self.logger.info(f"任务同步完成: 新增{stats['added']}个, 更新{stats['updated']}个, 删除{stats['removed']}个")
            
            return stats
            
        except Exception as e:
            self.logger.error(f"同步任务列表失败: {e}")
            return stats