#!/usr/bin/env python3
import sys
import os
import json
import traceback

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app, db
from app.models.user import User
from app.models.tenant import Tenant, UserTenant
from app.config import Config
import jwt
from datetime import datetime, timedelta

def generate_token(token_data):
    """生成JWT token"""
    token_data['exp'] = datetime.utcnow() + timedelta(hours=24)
    return jwt.encode(token_data, Config.JWT_SECRET_KEY, algorithm='HS256')

def test_tenant_creation():
    """测试租户创建API"""
    app = create_app()
    
    with app.app_context():
        # 删除并重新创建所有表
        db.drop_all()
        db.create_all()
        
        # 创建超级管理员
        super_admin = User(
            username='superadmin',
            email='super@test.com',
            role='admin'
        )
        super_admin.set_password('superpass')
        db.session.add(super_admin)
        db.session.commit()
        
        # 为超级管理员创建UserTenant记录
        tenant1 = Tenant(
            name='测试租户1',
            description='第一个测试租户'
        )
        db.session.add(tenant1)
        db.session.commit()
        
        super_admin_tenant = UserTenant(
            user_id=super_admin.id,
            tenant_id=tenant1.id,
            role='super_admin'
        )
        db.session.add(super_admin_tenant)
        db.session.commit()
        
        # 生成token
        token_data = {
            'user_id': super_admin.id,
            'username': super_admin.username,
            'role': super_admin.role,
            'tenant_role': 'super_admin'
        }
        token = generate_token(token_data)
        headers = {'Authorization': f'Bearer {token}'}
        
        # 测试数据
        tenant_data = {
            'name': '新测试租户',
            'description': '新创建的测试租户',
            'max_users': 20,
            'admin': {
                'username': 'new_admin',
                'email': 'new_admin@test.com',
                'password': 'password123'
            }
        }
        
        # 创建测试客户端
        client = app.test_client()
        
        try:
            response = client.post('/api/v1/tenants',
                                 data=json.dumps(tenant_data),
                                 content_type='application/json',
                                 headers=headers)
            
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.get_json()}")
            
            if response.status_code != 201:
                print(f"Error: Expected 201, got {response.status_code}")
            else:
                print("Success: Tenant created successfully")
                
        except Exception as e:
            print(f"Exception occurred: {e}")
            traceback.print_exc()

if __name__ == '__main__':
    test_tenant_creation()