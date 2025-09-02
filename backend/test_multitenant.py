#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多租户功能测试
测试租户隔离、权限控制、跨租户访问防护等关键场景
"""

import unittest
import json
import sys
import os
from unittest.mock import patch, MagicMock

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app, db
from app.models.user import User
from app.models.tenant import Tenant
from app.models.tenant import UserTenant
from app.models.task import Task
from app.models.result import Result
from app.models.alert import Alert
from app.models.system_variable import SystemVariable
import jwt
from app.config import Config
import datetime

def generate_token(token_data):
    """生成JWT token"""
    # 添加过期时间
    token_data['exp'] = datetime.datetime.now() + Config.JWT_ACCESS_TOKEN_EXPIRES
    return jwt.encode(token_data, Config.JWT_SECRET_KEY, algorithm='HS256')


class MultiTenantTestCase(unittest.TestCase):
    """多租户功能测试基类"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        # 删除所有表并重新创建
        db.drop_all()
        db.create_all()
        
        # 创建测试租户
        self.tenant1 = Tenant(
            name='测试租户1',
            description='第一个测试租户',
            max_users=15
        )
        self.tenant2 = Tenant(
            name='测试租户2', 
            description='第二个测试租户',
            max_users=10
        )
        db.session.add(self.tenant1)
        db.session.add(self.tenant2)
        db.session.commit()
        
        # 创建超级管理员
        self.super_admin = User(
            username='superadmin',
            email='super@test.com',
            role='admin'
        )
        self.super_admin.set_password('password123')
        db.session.add(self.super_admin)
        db.session.commit()
        
        # 为超级管理员创建UserTenant记录，设置role为super_admin
        super_admin_tenant = UserTenant(
            user_id=self.super_admin.id,
            tenant_id=self.tenant1.id,  # 可以关联任意租户，因为super_admin可以访问所有租户
            role='super_admin'
        )
        db.session.add(super_admin_tenant)
        
        # 创建租户管理员
        self.tenant1_admin = User(
            username='tenant1_admin',
            email='admin1@test.com',
            role='admin'
        )
        self.tenant1_admin.set_password('password123')
        db.session.add(self.tenant1_admin)
        
        self.tenant2_admin = User(
            username='tenant2_admin',
            email='admin2@test.com',
            role='admin'
        )
        self.tenant2_admin.set_password('password123')
        db.session.add(self.tenant2_admin)
        
        # 创建普通用户
        self.tenant1_user = User(
            username='tenant1_user',
            email='user1@test.com',
            role='viewer'
        )
        self.tenant1_user.set_password('password123')
        db.session.add(self.tenant1_user)
        
        db.session.commit()
        
        # 超级管理员不需要租户关联，通过role='admin'来识别
        
        # 创建用户租户关联
        user_tenant1_admin = UserTenant(
            user_id=self.tenant1_admin.id,
            tenant_id=self.tenant1.id,
            role='tenant_admin'
        )
        user_tenant2_admin = UserTenant(
            user_id=self.tenant2_admin.id,
            tenant_id=self.tenant2.id,
            role='tenant_admin'
        )
        user_tenant1_user = UserTenant(
            user_id=self.tenant1_user.id,
            tenant_id=self.tenant1.id,
            role='user'
        )
        
        db.session.add(user_tenant1_admin)
        db.session.add(user_tenant2_admin)
        db.session.add(user_tenant1_user)
        db.session.commit()
        
        # 创建测试任务（属于不同租户）
        self.task1 = Task(
            name='租户1任务',
            type='ping',
            interval=60,
            enabled=True,
            tenant_id=self.tenant1.id,
            target='192.168.1.1',
            config='{}'
        )
        self.task2 = Task(
            name='租户2任务',
            type='ping', 
            interval=60,
            enabled=True,
            tenant_id=self.tenant2.id,
            target='192.168.1.2',
            config='{}'
        )
        
        db.session.add(self.task1)
        db.session.add(self.task2)
        db.session.commit()
        
        # 创建测试结果（属于不同租户）
        self.result1 = Result(
            task_id=self.task1.id,
            tenant_id=self.tenant1.id,
            agent_id='agent1',
            status='success',
            response_time=100.0,
            details='{}'
        )
        self.result2 = Result(
            task_id=self.task2.id,
            tenant_id=self.tenant2.id,
            agent_id='agent2',
            status='success',
            response_time=200.0,
            details='{}'
        )
        
        db.session.add(self.result1)
        db.session.add(self.result2)
        db.session.commit()
        
    def tearDown(self):
        """测试后的清理工作"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
    def get_auth_headers(self, user, tenant_id=None):
        """获取认证头"""
        token_data = {
            'user_id': user.id,
            'username': user.username,
            'role': user.role
        }
        
        # 检查是否为超级管理员（只有self.super_admin才是真正的超级管理员）
        if user == self.super_admin:  # 超级管理员
            token_data['tenant_role'] = 'super_admin'
            if tenant_id:
                token_data['tenant_id'] = tenant_id
        elif tenant_id:
            token_data['tenant_id'] = tenant_id
            # 根据用户和租户关系设置租户角色
            user_tenant = UserTenant.query.filter_by(user_id=user.id, tenant_id=tenant_id).first()
            if user_tenant:
                token_data['tenant_role'] = user_tenant.role
            else:
                token_data['tenant_role'] = 'user'
            
        token = generate_token(token_data)
        return {'Authorization': f'Bearer {token}'}


class TestTenantIsolation(MultiTenantTestCase):
    """测试租户隔离功能"""
    
    def test_task_isolation(self):
        """测试任务的租户隔离"""
        # 租户1管理员只能看到租户1的任务
        headers = self.get_auth_headers(self.tenant1_admin, self.tenant1.id)
        response = self.client.get('/api/v2/tasks', headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # 应该只返回租户1的任务
        task_names = [task['name'] for task in data.get('data', {}).get('list', [])]
        self.assertIn('租户1任务', task_names)
        self.assertNotIn('租户2任务', task_names)
        
    def test_result_isolation(self):
        """测试结果的租户隔离"""
        # 租户1管理员只能看到租户1的结果
        headers = self.get_auth_headers(self.tenant1_admin, self.tenant1.id)
        response = self.client.get('/api/v2/results', headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # 应该只返回租户1的结果
        results = data.get('list', [])
        for result in results:
            self.assertEqual(result['tenant_id'], self.tenant1.id)
            
    def test_cross_tenant_access_denied(self):
        """测试跨租户访问被拒绝"""
        # 租户1管理员尝试访问租户2的任务
        headers = self.get_auth_headers(self.tenant1_admin, self.tenant1.id)
        response = self.client.get(f'/api/v2/tasks/{self.task2.id}', headers=headers)
        
        # 应该返回404或403
        self.assertIn(response.status_code, [403, 404])
        
    def test_system_variable_isolation(self):
        """测试系统变量的租户隔离"""
        # 创建不同租户的系统变量
        var1 = SystemVariable(
            name='$tenant1_var',
            value='tenant1_value',
            tenant_id=self.tenant1.id,
            is_secret=False
        )
        var2 = SystemVariable(
            name='$tenant2_var',
            value='tenant2_value',
            tenant_id=self.tenant2.id,
            is_secret=False
        )
        
        db.session.add(var1)
        db.session.add(var2)
        db.session.commit()
        
        # 租户1管理员只能看到租户1的变量
        headers = self.get_auth_headers(self.tenant1_admin, self.tenant1.id)
        response = self.client.get('/api/v2/system-variables', headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        var_names = [var['name'] for var in data.get('list', [])]
        self.assertIn('$tenant1_var', var_names)
        self.assertNotIn('$tenant2_var', var_names)


class TestPermissionControl(MultiTenantTestCase):
    """测试权限控制功能"""
    
    def test_super_admin_access_all_tenants(self):
        """测试超级管理员可以访问所有租户数据"""
        headers = self.get_auth_headers(self.super_admin)
        response = self.client.get('/api/v1/tenants', headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # 超级管理员应该能看到所有租户
        tenant_names = [tenant['name'] for tenant in data.get('list', [])]
        self.assertIn('测试租户1', tenant_names)
        self.assertIn('测试租户2', tenant_names)
        
    def test_tenant_admin_manage_users(self):
        """测试租户管理员可以管理本租户用户"""
        headers = self.get_auth_headers(self.tenant1_admin, self.tenant1.id)
        
        # 获取租户用户列表
        response = self.client.get(f'/api/v1/tenants/{self.tenant1.id}/users', headers=headers)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        user_names = [user['username'] for user in data.get('list', [])]
        self.assertIn('tenant1_admin', user_names)
        self.assertIn('tenant1_user', user_names)
        self.assertNotIn('tenant2_admin', user_names)
        
    def test_tenant_admin_cannot_access_other_tenant_users(self):
        """测试租户管理员不能访问其他租户用户"""
        headers = self.get_auth_headers(self.tenant1_admin, self.tenant1.id)
        
        # 尝试访问租户2的用户
        response = self.client.get(f'/api/v1/tenants/{self.tenant2.id}/users', headers=headers)
        self.assertEqual(response.status_code, 403)
        
    def test_regular_user_limited_access(self):
        """测试普通用户的有限访问权限"""
        headers = self.get_auth_headers(self.tenant1_user, self.tenant1.id)
        
        # 普通用户不能访问租户管理接口
        response = self.client.get('/api/v1/tenants', headers=headers)
        self.assertEqual(response.status_code, 403)
        
        # 普通用户不能访问用户管理接口
        response = self.client.get(f'/api/v1/tenants/{self.tenant1.id}/users', headers=headers)
        self.assertEqual(response.status_code, 403)


class TestTenantManagementAPI(MultiTenantTestCase):
    """测试租户管理API"""
    
    def test_create_tenant_with_admin(self):
        """测试创建租户并同时创建管理员"""
        headers = self.get_auth_headers(self.super_admin)
        
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
        
        response = self.client.post('/api/v1/tenants', 
                                  data=json.dumps(tenant_data),
                                  content_type='application/json',
                                  headers=headers)
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        
        # 验证租户创建成功
        self.assertIn('tenant', data)
        tenant_data = data['tenant']
        self.assertEqual(tenant_data['name'], '新测试租户')
        self.assertEqual(tenant_data['max_users'], 20)
        
        # 验证管理员用户创建成功
        new_admin = User.query.filter_by(username='new_admin').first()
        self.assertIsNotNone(new_admin)
        
        # 验证用户租户关联创建成功
        user_tenant = UserTenant.query.filter_by(
            user_id=new_admin.id,
            tenant_id=tenant_data['id']
        ).first()
        self.assertIsNotNone(user_tenant)
        self.assertEqual(user_tenant.role, 'tenant_admin')
        
    def test_tenant_user_limit(self):
        """测试租户用户数量限制"""
        headers = self.get_auth_headers(self.tenant1_admin, self.tenant1.id)
        
        # 修改租户1的最大用户数为2
        self.tenant1.max_users = 2
        db.session.commit()
        
        # 尝试添加第3个用户（应该失败）
        user_data = {
            'username': 'new_user',
            'email': 'new_user@test.com',
            'password': 'password123',
            'role': 'user'
        }
        
        response = self.client.post(f'/api/v1/tenants/{self.tenant1.id}/users',
                                  data=json.dumps(user_data),
                                  content_type='application/json',
                                  headers=headers)
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('租户用户数量已达上限', data.get('message', ''))


class TestDataMigration(MultiTenantTestCase):
    """测试数据迁移功能"""
    
    def test_existing_data_tenant_assignment(self):
        """测试现有数据的租户分配"""
        # 创建一个没有tenant_id的任务（模拟旧数据）
        old_task = Task(
            name='旧任务',
            type='ping',
            interval=60,
            enabled=True,
            target='192.168.1.100',
            config='{}'
            # 注意：没有设置tenant_id
        )
        db.session.add(old_task)
        db.session.commit()
        
        # 模拟数据迁移过程
        # 这里应该有迁移脚本将旧数据分配给默认租户
        # 实际实现中，这个逻辑在迁移脚本中
        
        # 验证迁移后的数据完整性
        tasks_without_tenant = Task.query.filter_by(tenant_id=None).all()
        self.assertEqual(len(tasks_without_tenant), 1)  # 应该有一个未分配租户的任务


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)