#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

import json
import jwt
from datetime import datetime, timedelta
from app import create_app, db
from app.models.user import User
from app.models.tenant import Tenant, UserTenant
from app.models.task import Task
from app.config import Config

def generate_token(token_data):
    """生成JWT token"""
    token_data['exp'] = datetime.utcnow() + timedelta(hours=1)
    return jwt.encode(token_data, Config.JWT_SECRET_KEY, algorithm='HS256')

app = create_app()
with app.app_context():
    # 获取现有数据
    tenant1 = Tenant.query.filter_by(name='测试租户1').first()
    tenant1_admin = User.query.filter_by(username='tenant1_admin').first()
    
    if not tenant1 or not tenant1_admin:
        print("请先运行 debug_test.py 创建测试数据")
        sys.exit(1)
    
    print(f"租户1 ID: {tenant1.id}")
    print(f"管理员 ID: {tenant1_admin.id}")
    
    # 生成token
    token_data = {
        'user_id': tenant1_admin.id,
        'tenant_id': str(tenant1.id),
        'tenant_role': 'tenant_admin'
    }
    token = generate_token(token_data)
    print(f"生成的token: {token[:50]}...")
    
    # 创建测试客户端
    client = app.test_client()
    
    # 测试API调用
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print("\n调用 /api/v2/tasks API...")
    response = client.get('/api/v2/tasks', headers=headers)
    
    print(f"响应状态码: {response.status_code}")
    print(f"响应数据: {response.data.decode('utf-8')}")
    
    if response.status_code == 200:
        data = json.loads(response.data)
        tasks = data.get('data', {}).get('list', [])
        print(f"\n返回的任务数量: {len(tasks)}")
        for task in tasks:
            print(f"任务: {task.get('name')}, 租户ID: {task.get('tenant_id')}")
    else:
        print(f"API调用失败: {response.status_code}")