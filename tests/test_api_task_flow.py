#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API拨测功能流程测试脚本

此脚本用于测试API拨测功能的完整流程，包括：
1. 创建系统变量
2. 创建API拨测任务
3. 执行API拨测任务
4. 查看API拨测结果

使用方法：
    python test_api_task_flow.py
"""

import requests
import json
import time
import sys

# 配置信息
BACKEND_URL = "http://localhost:5000/api/v1"
AGENT_ID = "book"  # 替换为实际的agent_id

# 测试状态跟踪
test_results = {
    "create_system_variable": False,
    "create_api_task": False,
    "execute_api_task": False,
    "check_api_result": False
}

# 颜色输出函数
def print_color(text, color):
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "end": "\033[0m"
    }
    print(f"{colors.get(color, '')}{text}{colors['end']}")

# 步骤1: 创建系统变量
def create_system_variable():
    print_color("\n步骤1: 创建系统变量", "blue")
    
    # 定义系统变量数据
    variable_data = {
        "name": "$public_test_api_base_url",
        "value": "https://httpbin.org",
        "is_secret": False,
        "description": "API测试基础URL"
    }
    
    try:
        # 发送创建系统变量请求
        response = requests.post(
            f"{BACKEND_URL}/system/variables",
            json=variable_data
        )
        
        # 检查响应
        if response.status_code == 201 or response.status_code == 200:
            data = response.json()
            if data.get("code") == 0:
                print_color("  ✓ 系统变量创建成功", "green")
                test_results["create_system_variable"] = True
                return data.get("data", {}).get("id")
            else:
                print_color(f"  ✗ 系统变量创建失败: {data.get('message')}", "red")
        else:
            print_color(f"  ✗ 系统变量创建请求失败: HTTP {response.status_code}", "red")
            print(response.text)
    except Exception as e:
        print_color(f"  ✗ 系统变量创建异常: {str(e)}", "red")
    
    return None

# 步骤2: 创建API拨测任务
def create_api_task():
    print_color("\n步骤2: 创建API拨测任务", "blue")
    
    # 定义API拨测任务数据
    task_data = {
        "name": "API拨测测试任务",
        "type": "api",
        "target": "$public_test_api_base_url",
        "interval": 60,
        "enabled": True,
        "agent_ids": [AGENT_ID],
        "config": {
            "variables": [
                {
                    "name": "$test_value",
                    "value": "test123"
                }
            ],
            "steps": [
                {
                    "step_id": "step1",
                    "name": "获取IP信息",
                    "request": {
                        "url": "$public_test_api_base_url/ip",
                        "method": "GET",
                        "headers": {
                            "Content-Type": "application/json",
                            "User-Agent": "IT-Dialer-Test"
                        }
                    },
                    "assertions": [
                        {
                            "type": "status_code",
                            "target": "status_code",
                            "operator": "equals",
                            "expected": 200
                        },
                        {
                            "type": "json",
                            "target": "$.origin",
                            "operator": "exists",
                            "expected": True
                        }
                    ],
                    "variables": [
                        {
                            "name": "$ip",
                            "type": "json",
                            "expression": "$.origin"
                        }
                    ]
                },
                {
                    "step_id": "step2",
                    "name": "发送测试数据",
                    "request": {
                        "url": "$public_test_api_base_url/post",
                        "method": "POST",
                        "headers": {
                            "Content-Type": "application/json",
                            "User-Agent": "IT-Dialer-Test"
                        },
                        "body": {
                            "test_value": "$test_value",
                            "ip": "$ip"
                        }
                    },
                    "assertions": [
                        {
                            "type": "status_code",
                            "target": "status_code",
                            "operator": "equals",
                            "expected": 200
                        },
                        {
                            "type": "json",
                            "target": "$.json.test_value",
                            "operator": "equals",
                            "expected": "$test_value"
                        }
                    ]
                }
            ]
        }
    }
    
    try:
        # 发送创建任务请求
        response = requests.post(
            f"{BACKEND_URL}/tasks",
            json=task_data
        )
        
        # 检查响应
        if response.status_code == 201 or response.status_code == 200:
            data = response.json()
            if data.get("code") == 0:
                print_color("  ✓ API拨测任务创建成功", "green")
                test_results["create_api_task"] = True
                return data.get("data", {}).get("id")
            else:
                print_color(f"  ✗ API拨测任务创建失败: {data.get('message')}", "red")
        else:
            print_color(f"  ✗ API拨测任务创建请求失败: HTTP {response.status_code}", "red")
            print(response.text)
    except Exception as e:
        print_color(f"  ✗ API拨测任务创建异常: {str(e)}", "red")
    
    return None

# 步骤3: 执行API拨测任务
def execute_api_task(task_id):
    print_color("\n步骤3: 执行API拨测任务", "blue")
    
    if not task_id:
        print_color("  ✗ 无法执行任务: 任务ID为空", "red")
        return False
    
    # 定义执行任务数据
    execute_data = {
        "task_id": task_id
    }
    
    try:
        # 发送执行任务请求
        response = requests.post(
            f"{BACKEND_URL}/tasks/execute",
            json=execute_data
        )
        
        # 检查响应
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 0:
                print_color("  ✓ API拨测任务执行请求成功", "green")
                print_color("  等待任务执行完成...", "yellow")
                time.sleep(5)  # 等待任务执行完成
                test_results["execute_api_task"] = True
                return True
            else:
                print_color(f"  ✗ API拨测任务执行请求失败: {data.get('message')}", "red")
        else:
            print_color(f"  ✗ API拨测任务执行请求失败: HTTP {response.status_code}", "red")
            print(response.text)
    except Exception as e:
        print_color(f"  ✗ API拨测任务执行异常: {str(e)}", "red")
    
    return False

# 步骤4: 查看API拨测结果
def check_api_result(task_id):
    print_color("\n步骤4: 查看API拨测结果", "blue")
    
    if not task_id:
        print_color("  ✗ 无法查看结果: 任务ID为空", "red")
        return False
    
    try:
        # 发送查询结果请求
        response = requests.get(
            f"{BACKEND_URL}/results?task_id={task_id}&latest=true"
        )
        
        # 检查响应
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 0 and data.get("data", {}).get("list"):
                results = data.get("data", {}).get("list", [])
                if results:
                    result = results[0]
                    print_color("  ✓ 成功获取API拨测结果", "green")
                    print_color(f"    - 任务ID: {result.get('task_id')}", "yellow")
                    print_color(f"    - 执行状态: {result.get('status')}", "yellow")
                    print_color(f"    - 响应时间: {result.get('response_time')}ms", "yellow")
                    print_color(f"    - 执行节点: {result.get('agent_area')}", "yellow")
                    
                    # 解析详细结果
                    details = result.get('details')
                    if isinstance(details, str):
                        try:
                            details = json.loads(details)
                        except:
                            details = {}
                    
                    if details and details.get('steps'):
                        steps = details.get('steps', [])
                        print_color(f"    - 步骤数量: {len(steps)}", "yellow")
                        
                        for i, step in enumerate(steps):
                            print_color(f"      步骤 {i+1}: {step.get('name')}", "yellow")
                            print_color(f"        状态: {step.get('status')}", "yellow")
                            if step.get('response'):
                                print_color(f"        状态码: {step.get('response').get('status_code')}", "yellow")
                                print_color(f"        响应时间: {step.get('response').get('elapsed')}ms", "yellow")
                    
                    test_results["check_api_result"] = True
                    return True
                else:
                    print_color("  ✗ 未找到API拨测结果", "red")
            else:
                print_color(f"  ✗ 获取API拨测结果失败: {data.get('message')}", "red")
        else:
            print_color(f"  ✗ 获取API拨测结果请求失败: HTTP {response.status_code}", "red")
            print(response.text)
    except Exception as e:
        print_color(f"  ✗ 获取API拨测结果异常: {str(e)}", "red")
    
    return False

# 主函数
def main():
    print_color("开始API拨测功能流程测试", "blue")
    
    # 步骤1: 创建系统变量
    variable_id = create_system_variable()
    
    # 步骤2: 创建API拨测任务
    task_id = create_api_task()
    
    # 步骤3: 执行API拨测任务
    if task_id:
        execute_success = execute_api_task(task_id)
    else:
        execute_success = False
        print_color("  ✗ 跳过执行任务步骤: 任务创建失败", "red")
    
    # 步骤4: 查看API拨测结果
    if task_id and execute_success:
        check_api_result(task_id)
    else:
        print_color("  ✗ 跳过查看结果步骤: 任务执行失败", "red")
    
    # 输出测试结果摘要
    print_color("\nAPI拨测功能流程测试结果摘要:", "blue")
    for step, result in test_results.items():
        status = "✓ 通过" if result else "✗ 失败"
        color = "green" if result else "red"
        print_color(f"  {status} {step.replace('_', ' ').title()}", color)
    
    # 判断整体测试是否通过
    if all(test_results.values()):
        print_color("\n✓ 所有测试通过! API拨测功能正常工作。", "green")
        return 0
    else:
        print_color("\n✗ 测试失败! 请检查上述错误信息。", "red")
        return 1

if __name__ == "__main__":
    sys.exit(main())