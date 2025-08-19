#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试任务状态告警和超时告警功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.task import Task
from app.services.alert_matcher import alert_matcher
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_task_alerts():
    """测试任务告警功能"""
    app = create_app()
    
    with app.app_context():
        # 创建测试任务
        test_config = {
            "statusAlertConfig": ["failed"],
            "timeoutAlertEnabled": True,
            "timeoutThreshold": 3000,  # 3秒
            "steps": [
                {
                    "step_id": "step1",
                    "name": "测试步骤",
                    "method": "GET",
                    "url": "http://example.com"
                }
            ]
        }
        
        task = Task(
            name="测试任务告警",
            type="api",
            target="http://example.com",
            interval=60,
            enabled=True,
            config=json.dumps(test_config)
        )
        
        # 测试1: 任务失败状态告警
        print("\n=== 测试1: 任务失败状态告警 ===")
        result_data_failed = {
            "status": "failed",
            "response_time": 2.5,
            "message": "连接失败"
        }
        
        print(f"调用process_result，任务配置: {task.get_config()}")
        alerts = alert_matcher.process_result(result_data_failed, task)
        print(f"生成告警数量: {len(alerts)}")
        for alert in alerts:
            print(f"告警类型: {alert.alert_type}")
            print(f"告警级别: {alert.alert_level}")
            print(f"告警标题: {alert.title}")
            print(f"告警内容: {alert.content}")
            print(f"触发值: {alert.trigger_value}")
            print(f"阈值: {alert.threshold_value}")
            print("---")
        
        # 测试2: 任务超时告警
        print("\n=== 测试2: 任务超时告警 ===")
        result_data_timeout = {
            "status": "success",
            "response_time": 5.2,  # 5.2秒，超过3秒阈值
            "message": "请求成功但响应慢"
        }
        
        alerts = alert_matcher.process_result(result_data_timeout, task)
        print(f"生成告警数量: {len(alerts)}")
        for alert in alerts:
            print(f"告警类型: {alert.alert_type}")
            print(f"告警级别: {alert.alert_level}")
            print(f"告警标题: {alert.title}")
            print(f"告警内容: {alert.content}")
            print(f"触发值: {alert.trigger_value}")
            print(f"阈值: {alert.threshold_value}")
            print("---")
        
        # 测试3: 同时触发状态告警和超时告警
        print("\n=== 测试3: 同时触发状态告警和超时告警 ===")
        result_data_both = {
            "status": "failed",
            "response_time": 6.8,  # 超过3秒阈值
            "message": "HTTPConnectionPool(host='localhost', port=6000): Max retries exceeded"
        }
        
        alerts = alert_matcher.process_result(result_data_both, task)
        print(f"生成告警数量: {len(alerts)}")
        for alert in alerts:
            print(f"告警类型: {alert.alert_type}")
            print(f"告警级别: {alert.alert_level}")
            print(f"告警标题: {alert.title}")
            print(f"告警内容: {alert.content}")
            print(f"触发值: {alert.trigger_value}")
            print(f"阈值: {alert.threshold_value}")
            print("---")
        
        # 测试4: 正常情况，不触发告警
        print("\n=== 测试4: 正常情况，不触发告警 ===")
        result_data_normal = {
            "status": "success",
            "response_time": 1.2,  # 小于3秒阈值
            "message": "请求成功"
        }
        
        alerts = alert_matcher.process_result(result_data_normal, task)
        print(f"生成告警数量: {len(alerts)}")
        
        print("\n测试完成！")

if __name__ == "__main__":
    test_task_alerts()