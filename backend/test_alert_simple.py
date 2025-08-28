#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的告警匹配功能测试
"""

import requests
import json
from datetime import datetime
import time

# 配置
BASE_URL = 'http://127.0.0.1:5000/api/v1'
HEADERS = {'Content-Type': 'application/json'}

def test_simple_alert():
    print("开始简化告警测试...")
    
    # 1. 创建测试任务
    task_data = {
        'name': '简单告警测试',
        'type': 'api',
        'target': 'https://httpbin.org',
        'interval': 60,
        'enabled': True,
        'agent_ids': ['book'],
        'config': {
            'steps': [{
                'step_id': 'step1',
                'name': '测试步骤',
                'request': {
                    'url': 'https://httpbin.org/get',
                    'method': 'GET'
                }
            }]
        }
    }
    
    response = requests.post(f'{BASE_URL}/tasks', json=task_data, headers=HEADERS)
    if response.status_code != 201:
        print(f"创建任务失败: {response.text}")
        return
    
    task = response.json()['data']
    task_id = task['id']
    print(f"任务创建成功，ID: {task_id}")
    
    # 2. 创建状态码告警配置
    alert_config = {
        'task_id': task_id,
        'step_id': 'step1',
        'alert_type': 'status_code',
        'enabled': True,
        'config': {
            'allowed_codes': [200],
            'level': 'warning'
        }
    }
    
    response = requests.post(f'{BASE_URL}/alert-configs', json=alert_config, headers=HEADERS)
    if response.status_code != 200:
        print(f"创建告警配置失败: {response.text}")
        return
    print("告警配置创建成功")
    
    # 3. 上报异常结果（状态码500）
    result_data = {
        'task_id': task_id,
        'status': 'failed',
        'response_time': 500,
        'message': '测试失败',
        'agent_id': 'book',
        'agent_area': 'guangzhou',
        'details': {
            'steps': [{
                'step_id': 'step1',
                'name': '测试步骤',
                'response_time': 500,
                'response': {
                    'status_code': 500,  # 异常状态码
                    'headers': {'Content-Type': 'application/json'},
                    'body': '{"error": "server error"}'
                }
            }]
        }
    }
    
    print("上报异常结果...")
    response = requests.post(f'{BASE_URL}/results', json=result_data, headers=HEADERS)
    if response.status_code != 201:
        print(f"上报结果失败: {response.text}")
        return
    print("结果上报成功")
    
    # 4. 等待并检查告警
    print("等待告警处理...")
    time.sleep(3)
    
    response = requests.get(f'{BASE_URL}/alerts', headers=HEADERS)
    if response.status_code != 200:
        print(f"获取告警失败: {response.text}")
        return
    
    alerts_data = response.json()['data']
    alerts = alerts_data.get('alerts', [])
    
    print(f"\n告警数量: {len(alerts)}")
    for alert in alerts:
        print(f"- ID: {alert['id']}")
        print(f"  任务ID: {alert['task_id']}")
        print(f"  步骤ID: {alert.get('step_id', 'N/A')}")
        print(f"  类型: {alert['alert_type']}")
        print(f"  标题: {alert['title']}")
        print(f"  内容: {alert['content']}")
        print(f"  触发值: {alert.get('trigger_value', 'N/A')}")
        print(f"  阈值: {alert.get('threshold_value', 'N/A')}")
        print()
    
    # 5. 清理
    print("清理测试数据...")
    requests.delete(f'{BASE_URL}/tasks/{task_id}', headers=HEADERS)
    print("测试完成")

if __name__ == '__main__':
    test_simple_alert()