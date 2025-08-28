#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
告警匹配功能测试脚本
"""

import requests
import json
from datetime import datetime

# 配置
BASE_URL = 'http://127.0.0.1:5000/api/v1'
HEADERS = {'Content-Type': 'application/json'}

def test_alert_matching():
    """
    测试告警匹配功能
    """
    print("开始测试告警匹配功能...")
    
    # 1. 创建测试任务
    print("\n1. 创建测试任务")
    task_data = {
        'name': '告警测试任务',
        'type': 'api',
        'target': 'https://httpbin.org',
        'interval': 60,
        'enabled': True,
        'agent_ids': ['book'],
        'config': {
            'steps': [
                {
                    'step_id': 'step1',
                    'name': '测试步骤1',
                    'request': {
                        'url': 'https://httpbin.org/status/500',
                        'method': 'GET'
                    }
                }
            ]
        }
    }
    
    response = requests.post(f'{BASE_URL}/tasks', json=task_data, headers=HEADERS)
    if response.status_code != 201:
        print(f"创建任务失败: {response.text}")
        return
    
    task = response.json()['data']
    task_id = task['id']
    print(f"任务创建成功，ID: {task_id}")
    
    # 2. 创建告警配置
    print("\n2. 创建告警配置")
    
    # 状态码告警配置
    status_code_config = {
        'task_id': task_id,
        'step_id': 'step1',
        'alert_type': 'status_code',
        'enabled': True,
        'config': {
            'allowed_codes': [200, 201, 202],
            'level': 'warning'
        }
    }
    
    response = requests.post(f'{BASE_URL}/alert-configs', json=status_code_config, headers=HEADERS)
    if response.status_code != 200:
        print(f"创建状态码告警配置失败: {response.text}")
        return
    print("状态码告警配置创建成功")
    
    # 响应时间告警配置
    response_time_config = {
        'task_id': task_id,
        'step_id': 'step1',
        'alert_type': 'response_time',
        'enabled': True,
        'config': {
            'threshold': 100,  # 100ms阈值
            'level': 'warning'
        }
    }
    
    response = requests.post(f'{BASE_URL}/alert-configs', json=response_time_config, headers=HEADERS)
    if response.status_code != 200:
        print(f"创建响应时间告警配置失败: {response.text}")
        return
    print("响应时间告警配置创建成功")
    
    # 3. 模拟agent上报结果数据（触发告警）
    print("\n3. 模拟agent上报异常结果数据")
    
    result_data = {
        'task_id': task_id,
        'status': 'failed',
        'response_time': 1500,  # 超过阈值
        'message': '任务执行失败',
        'agent_id': 'test-agent-001',
        'agent_area': '测试区域',
        'details': {
            'steps': [
                {
                    'step_id': 'step1',
                    'name': '测试步骤1',
                    'response_time': 1500,
                    'response': {
                        'status_code': 500,  # 异常状态码
                        'headers': {'Content-Type': 'application/json'},
                        'body': '{"error": "Internal Server Error"}'
                    },
                    'assertions': [
                        {
                            'source': 'status_code',
                            'comparison': 'equal',
                            'target': '200',
                            'result': False,
                            'message': '状态码不等于200',
                            'actual': '500',
                            'expected': '200',
                            'enableAlert': True,
                            'alertCondition': 'not_match'
                        }
                    ]
                }
            ]
        }
    }
    
    response = requests.post(f'{BASE_URL}/results', json=result_data, headers=HEADERS)
    if response.status_code != 201:
        print(f"上报结果失败: {response.text}")
        return
    print("结果上报成功")
    
    # 4. 检查生成的告警
    print("\n4. 检查生成的告警")
    
    # 等待一下让告警处理完成
    import time
    time.sleep(2)
    
    response = requests.get(f'{BASE_URL}/alerts?task_name=告警测试任务', headers=HEADERS)
    if response.status_code != 200:
        print(f"获取告警列表失败: {response.text}")
        return
    
    alerts_data = response.json()['data']
    alerts = alerts_data['items']
    
    print(f"生成的告警数量: {len(alerts)}")
    for alert in alerts:
        print(f"- 告警类型: {alert['alert_type']}")
        print(f"  标题: {alert['title']}")
        print(f"  内容: {alert['content']}")
        print(f"  触发值: {alert['trigger_value']}")
        print(f"  阈值: {alert['threshold_value']}")
        print(f"  级别: {alert['alert_level']}")
        print(f"  状态: {alert['status']}")
        print()
    
    # 5. 测试正常情况（不触发告警）
    print("\n5. 模拟agent上报正常结果数据")
    
    normal_result_data = {
        'task_id': task_id,
        'status': 'success',
        'response_time': 50,  # 正常响应时间
        'message': '任务执行成功',
        'agent_id': 'test-agent-001',
        'agent_area': '测试区域',
        'details': {
            'steps': [
                {
                    'step_id': 'step1',
                    'name': '测试步骤1',
                    'response_time': 50,
                    'response': {
                        'status_code': 200,  # 正常状态码
                        'headers': {'Content-Type': 'application/json'},
                        'body': '{"status": "ok"}'
                    },
                    'assertions': [
                        {
                            'source': 'status_code',
                            'comparison': 'equal',
                            'target': '200',
                            'result': True,
                            'message': '状态码等于200',
                            'actual': '200',
                            'expected': '200',
                            'enableAlert': True,
                            'alertCondition': 'not_match'
                        }
                    ]
                }
            ]
        }
    }
    
    response = requests.post(f'{BASE_URL}/results', json=normal_result_data, headers=HEADERS)
    if response.status_code != 201:
        print(f"上报正常结果失败: {response.text}")
        return
    print("正常结果上报成功")
    
    # 6. 再次检查告警（应该没有新增）
    print("\n6. 再次检查告警数量")
    time.sleep(2)
    
    response = requests.get(f'{BASE_URL}/alerts?task_name=告警测试任务', headers=HEADERS)
    if response.status_code != 200:
        print(f"获取告警列表失败: {response.text}")
        return
    
    new_alerts_data = response.json()['data']
    new_alerts = new_alerts_data['items']
    
    print(f"当前告警总数: {len(new_alerts)}")
    print(f"新增告警数: {len(new_alerts) - len(alerts)}")
    
    # 7. 清理测试数据
    print("\n7. 清理测试数据")
    
    # 删除任务（会级联删除相关数据）
    response = requests.delete(f'{BASE_URL}/tasks/{task_id}', headers=HEADERS)
    if response.status_code == 200:
        print("测试数据清理成功")
    else:
        print(f"清理测试数据失败: {response.text}")
    
    print("\n告警匹配功能测试完成！")


if __name__ == '__main__':
    test_alert_matching()