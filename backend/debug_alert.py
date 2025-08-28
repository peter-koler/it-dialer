#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试告警功能
"""

import logging
import sys
import os

# 添加app目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app, db
from app.models.task import Task
from app.services.alert_matcher import alert_matcher

# 设置日志级别
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_task4_alert():
    """调试任务4的告警功能"""
    app = create_app()
    
    with app.app_context():
        # 获取任务4
        task = Task.query.get(4)
        if not task:
            logger.error("任务4不存在")
            return
        
        logger.info(f"找到任务4: {task.name}")
        logger.info(f"任务配置: {task.get_config()}")
        
        # 模拟agent上报的失败结果
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
        
        logger.info("开始处理告警匹配...")
        
        # 调用告警匹配器
        alerts = alert_matcher.process_result(result_data, task)
        
        logger.info(f"告警匹配完成，生成了 {len(alerts)} 个告警")
        
        for i, alert in enumerate(alerts):
            logger.info(f"告警 {i+1}: 类型={alert.alert_type}, 级别={alert.alert_level}, 标题={alert.title}")
        
        if alerts:
            logger.info("保存告警到数据库...")
            alert_matcher.save_alerts(alerts)
            logger.info("告警保存完成")
        else:
            logger.warning("没有生成任何告警")

if __name__ == '__main__':
    debug_task4_alert()