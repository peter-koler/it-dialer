#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_login():
    """测试登录接口"""
    url = "http://localhost:5001/api/v1/auth/login"
    
    # 测试数据
    test_cases = [
        {"username": "boc", "password": "123456", "description": "普通用户boc"},
        {"username": "test", "password": "123456", "description": "管理员test"},
        {"username": "ceshi1", "password": "123456", "description": "普通用户ceshi1"},
        {"username": "superadmin", "password": "123456", "description": "超级管理员superadmin"},
    ]
    
    for case in test_cases:
        print(f"\n测试 {case['description']}:")
        print(f"用户名: {case['username']}, 密码: {case['password']}")
        
        try:
            response = requests.post(
                url,
                json={
                    "username": case["username"],
                    "password": case["password"]
                },
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    print("✅ 登录成功")
                else:
                    print(f"❌ 登录失败: {data.get('message')}")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求异常: {e}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析错误: {e}")
        except Exception as e:
            print(f"❌ 其他错误: {e}")

if __name__ == "__main__":
    print("开始测试登录接口...")
    test_login()
    print("\n测试完成")