#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试任务4的告警功能
"""

import requests
import json
import time
from datetime import datetime

# 配置
BASE_URL = 'http://localhost:5000/api/v1'
HEADERS = {'Content-Type': 'application/json'}

def test_task4_alert():
    """测试任务4的告警功能"""
    print("开始测试任务4的告警功能")
    
    # 1. 模拟agent上报任务4的失败结果
    print("\n1. 模拟agent上报任务4的失败结果")
    
    result_data = {
        'task_id': 4,
        'status': 'failed',
        'response_time': 1.75,
        'message': '步骤 \'获取主机名\' 失败: 执行异常: HTTPConnectionPool(host=\'localhost\', port=6000): Max retries exceeded with url: /name?ip=%24ip (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x101f645a0>: Failed to establish a new connection: [Errno 61] Connection refused\'))',
        'agent_id': 'test-agent',
        'agent_area': 'test-area',
        'details': {
            'steps': [
                {
                    'step_id': 'step_1755585696329_3mvgyxv63',
                    'name': '获取 ip 地址',
                    'status': 'failed',
                    'response_time': 0,
                    'message': '执行异常: HTTPConnectionPool(host=\'localhost\', port=6000): Max retries exceeded with url: /ip (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x101f60050>: Failed to establish a new connection: [Errno 61] Connection refused\'))',
                    'request': {
                        'body': '',
                        'contentType': 'application/json',
                        'headers': [],
                        'method': 'GET',
                        'params': [],
                        'url': 'http://localhost:6000/ip',
                        'urlParameters': []
                    },
                    'response': {},
                    'assertions': [],
                    'extractions': []
                },
                {
                    'step_id': 'step_1755585966494_mj4x35gnh',
                    'name': '获取主机名',
                    'status': 'failed',
                    'response_time': 0,
                    'message': '执行异常: HTTPConnectionPool(host=\'localhost\', port=6000): Max retries exceeded with url: /name?ip=%24ip (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x101f645a0>: Failed to establish a new connection: [Errno 61] Connection refused\'))',
                    'request': {
                        'body': '',
                        'contentType': 'application/json',
                        'headers': [],
                        'method': 'GET',
                        'params': [{'key': 'ip', 'value': '$ip'}],
                        'url': 'http://localhost:6000/name',
                        'urlParameters': [{'key': 'ip', 'value': '$ip'}]
                    },
                    'response': {},
                    'assertions': [],
                    'extractions': []
                }
            ],
            'variables': {'$public_test': 'abc'},
            'total_assertions': 0,
            'passed_assertions': 0,
            'start_time': '2025-08-19T14:22:53.392459',
            'end_time': '2025-08-19T14:22:53.394377'
        }
    }
    
    print(f"上报数据: {json.dumps(result_data, indent=2, ensure_ascii=False)}")
    
    response = requests.post(f'{BASE_URL}/results', json=result_data, headers=HEADERS)
    if response.status_code != 201:
        print(f"上报结果失败: {response.status_code} - {response.text}")
        return
    
    print("结果上报成功")
    
    # 2. 等待告警处理
    print("\n2. 等待告警处理...")
    time.sleep(3)
    
    # 3. 检查告警
    print("\n3. 检查告警")
    response = requests.get(f'{BASE_URL}/alerts?page=1&per_page=20', headers=HEADERS)
    if response.status_code != 200:
        print(f"获取告警失败: {response.status_code} - {response.text}")
        return
    
    response_data = response.json()
    print(f"API响应: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
    
    alerts_data = response_data['data']
    alerts = alerts_data.get('alerts', [])
    
    print(f"告警总数: {len(alerts)}")
    
    # 查找任务4相关的告警
    task4_alerts = [alert for alert in alerts if alert['task_id'] == 4]
    print(f"任务4相关告警数: {len(task4_alerts)}")
    
    for i, alert in enumerate(task4_alerts):
        print(f"\n告警 {i+1}:")
        print(f"  ID: {alert['id']}")
        print(f"  任务ID: {alert['task_id']}")
        print(f"  步骤ID: {alert.get('step_id', 'N/A')}")
        print(f"  类型: {alert['alert_type']}")
        print(f"  级别: {alert['alert_level']}")
        print(f"  标题: {alert['title']}")
        print(f"  内容: {alert['content']}")
        print(f"  触发值: {alert.get('trigger_value', 'N/A')}")
        print(f"  阈值: {alert.get('threshold_value', 'N/A')}")
        print(f"  创建时间: {alert['created_at']}")
    
    if len(task4_alerts) == 0:
        print("\n❌ 没有找到任务4的告警，可能存在问题")
    else:
        print(f"\n✅ 找到 {len(task4_alerts)} 个任务4的告警")
    
    print("\n测试完成！")

if __name__ == '__main__':
    test_task4_alert()