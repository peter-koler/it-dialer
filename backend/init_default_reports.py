#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化默认报表
为系统创建默认的报表配置，供前端导出功能使用
"""

import sys
import os
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.report import Report

def init_default_reports():
    """初始化默认报表"""
    app = create_app()
    
    with app.app_context():
        # 检查是否已存在默认报表
        existing_reports = Report.query.filter(
            Report.type.in_([
                'overview',
                'tcp', 
                'ping',
                'http',
                'api'
            ])
        ).all()
        
        if existing_reports:
            print(f"已存在 {len(existing_reports)} 个默认报表，跳过初始化")
            return
    
        # 创建默认报表配置
        default_reports = [
            {
                'type': 'overview',
                'task_ids': json.dumps([]),
                'time_range': json.dumps({
                    'type': 'last_7_days',
                    'start_date': None,
                    'end_date': None
                }),
                'metrics': json.dumps({
                    'include_success_rate': True,
                    'include_response_time': True,
                    'include_error_analysis': True
                })
            },
            {
                'type': 'tcp',
                'task_ids': json.dumps([]),
                'time_range': json.dumps({
                    'type': 'last_30_days',
                    'start_date': None,
                    'end_date': None
                }),
                'metrics': json.dumps({
                    'include_connection_time': True,
                    'include_success_rate': True,
                    'include_port_analysis': True
                })
            },
            {
                'type': 'ping',
                'task_ids': json.dumps([]),
                'time_range': json.dumps({
                    'type': 'last_30_days',
                    'start_date': None,
                    'end_date': None
                }),
                'metrics': json.dumps({
                    'include_latency': True,
                    'include_packet_loss': True,
                    'include_jitter': True
                })
            },
            {
                'type': 'http',
                'task_ids': json.dumps([]),
                'time_range': json.dumps({
                    'type': 'last_30_days',
                    'start_date': None,
                    'end_date': None
                }),
                'metrics': json.dumps({
                    'include_response_time': True,
                    'include_status_codes': True,
                    'include_content_analysis': True
                })
            },
            {
                'type': 'api',
                'task_ids': json.dumps([]),
                'time_range': json.dumps({
                    'type': 'last_30_days',
                    'start_date': None,
                    'end_date': None
                }),
                'metrics': json.dumps({
                    'include_response_time': True,
                    'include_success_rate': True,
                    'include_error_analysis': True
                })
            }
        ]
        
        # 创建报表记录
        created_count = 0
        for report_data in default_reports:
            try:
                report = Report(
                    type=report_data['type'],
                    task_ids=report_data['task_ids'],
                    time_range=report_data['time_range'],
                    metrics=report_data['metrics']
                )
                
                db.session.add(report)
                created_count += 1
                print(f"创建报表: {report_data['type']}")
                
            except Exception as e:
                print(f"创建报表失败 {report_data['type']}: {str(e)}")
                continue
        
        try:
            db.session.commit()
            print(f"\n成功初始化 {created_count} 个默认报表")
        except Exception as e:
            db.session.rollback()
            print(f"保存报表失败: {str(e)}")
            return False
        
        return True

def main():
    """主函数"""
    print("开始初始化默认报表...")
    
    try:
        success = init_default_reports()
        if success:
            print("默认报表初始化完成！")
        else:
            print("默认报表初始化失败！")
            sys.exit(1)
    except Exception as e:
        print(f"初始化过程中发生错误: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()