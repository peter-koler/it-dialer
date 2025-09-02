#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app, db
from app.models.user import User
from app.models.tenant import Tenant, UserTenant
from app.models.task import Task
import jwt
from app.config import Config
from datetime import datetime, timedelta
import json

app = create_app()
with app.app_context():
    # 删除并重新创建数据
    db.drop_all()
    db.create_all()
    
    # 创建租户
    tenant1 = Tenant(name='租户1', description='测试租户1', max_users=15)
    tenant2 = Tenant(name='租户2', description='测试租户2', max_users=15)
    db.session.add(tenant1)
    db.session.add(tenant2)
    db.session.commit()
    
    # 创建用户
    admin1 = User(username='admin1', email='admin1@test.com', role='admin')
    admin1.set_password('password')
    db.session.add(admin1)
    db.session.commit()
    
    # 创建用户租户关联
    user_tenant1 = UserTenant(user_id=admin1.id, tenant_id=tenant1.id, role='tenant_admin')
    db.session.add(user_tenant1)
    db.session.commit()
    
    # 创建任务
    task1 = Task(name='租户1任务', type='ping', target='192.168.1.1', tenant_id=tenant1.id)
    task2 = Task(name='租户2任务', type='ping', target='192.168.1.2', tenant_id=tenant2.id)
    db.session.add(task1)
    db.session.add(task2)
    db.session.commit()
    
    print(f"租户1 ID: {tenant1.id}")
    print(f"租户2 ID: {tenant2.id}")
    print(f"管理员1 ID: {admin1.id}")
    print(f"用户租户关联角色: {user_tenant1.role}")
    
    # 生成token
    token_data = {
        'user_id': admin1.id,
        'tenant_id': tenant1.id,
        'tenant_role': 'tenant_admin'  # 明确设置为tenant_admin
    }
    token_data['exp'] = datetime.utcnow() + timedelta(hours=1)
    token = jwt.encode(token_data, Config.JWT_SECRET_KEY, algorithm='HS256')
    print(f"生成的token数据: {token_data}")
    
    # 测试API调用
    with app.test_client() as client:
        headers = {'Authorization': f'Bearer {token}'}
        response = client.get('/api/v2/tasks', headers=headers)
        
        print(f"\n响应状态码: {response.status_code}")
        if response.status_code == 200:
            data = json.loads(response.data)
            print(f"响应数据: {data}")
            tasks = data.get('data', {}).get('list', [])
            print(f"\n返回的任务数量: {len(tasks)}")
            for task in tasks:
                print(f"任务: {task.get('name')}, 租户ID: {task.get('tenant_id')}")
        else:
            print(f"错误响应: {response.data.decode()}")