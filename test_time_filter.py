#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
from datetime import datetime, timedelta
from dateutil import parser

# 测试时间筛选功能
def test_time_filter():
    base_url = "http://localhost:5000/api/v1"
    
    # 测试1: 获取所有结果（无时间过滤）
    print("=== 测试1: 获取所有结果 ===")
    response = requests.get(f"{base_url}/results")
    if response.status_code == 200:
        data = response.json()
        print(f"总结果数: {data['data']['total']}")
        if data['data']['list']:
            for result in data['data']['list'][:3]:  # 显示前3条
                print(f"ID: {result['id']}, Task ID: {result['task_id']}, Created: {result['created_at']}")
    else:
        print(f"请求失败: {response.status_code}")
    
    # 测试2: 使用时间过滤（最近30天）
    print("\n=== 测试2: 最近30天的结果 ===")
    end_time = datetime.now()
    start_time = end_time - timedelta(days=30)
    
    params = {
        'start': start_time.isoformat(),
        'end': end_time.isoformat()
    }
    
    response = requests.get(f"{base_url}/results", params=params)
    if response.status_code == 200:
        data = response.json()
        print(f"最近30天结果数: {data['data']['total']}")
        if data['data']['list']:
            for result in data['data']['list'][:3]:  # 显示前3条
                print(f"ID: {result['id']}, Task ID: {result['task_id']}, Created: {result['created_at']}")
    else:
        print(f"请求失败: {response.status_code}")
    
    # 测试3: 使用时间过滤（最近1小时）
    print("\n=== 测试3: 最近1小时的结果 ===")
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=1)
    
    params = {
        'start': start_time.isoformat(),
        'end': end_time.isoformat()
    }
    
    response = requests.get(f"{base_url}/results", params=params)
    if response.status_code == 200:
        data = response.json()
        print(f"最近1小时结果数: {data['data']['total']}")
        if data['data']['list']:
            for result in data['data']['list'][:3]:  # 显示前3条
                print(f"ID: {result['id']}, Task ID: {result['task_id']}, Created: {result['created_at']}")
        else:
            print("没有找到最近1小时的数据")
    else:
        print(f"请求失败: {response.status_code}")
    
    # 测试4: 检查数据库中最新和最旧的数据时间
    print("\n=== 测试4: 数据时间范围分析 ===")
    response = requests.get(f"{base_url}/results?size=100")  # 获取更多数据
    if response.status_code == 200:
        data = response.json()
        if data['data']['list']:
            times = []
            for result in data['data']['list']:
                try:
                    dt = parser.isoparse(result['created_at'])
                    times.append(dt)
                except:
                    continue
            
            if times:
                times.sort()
                print(f"最早数据时间: {times[0]}")
                print(f"最新数据时间: {times[-1]}")
                print(f"当前时间: {datetime.now()}")
                
                # 计算时间差
                now = datetime.now()
                latest_diff = now - times[-1].replace(tzinfo=None)
                print(f"最新数据距离现在: {latest_diff}")

if __name__ == "__main__":
    test_time_filter()