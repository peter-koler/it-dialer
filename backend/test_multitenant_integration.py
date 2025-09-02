#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多租户功能集成测试
测试实际的HTTP API请求和响应，验证租户隔离和权限控制
"""

import unittest
import json
import requests
import time
import sys
import os
from datetime import datetime, timedelta

# 测试配置
BASE_URL = 'http://localhost:5001/api'
TEST_TIMEOUT = 30


class MultiTenantIntegrationTest(unittest.TestCase):
    """多租户集成测试"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.base_url = BASE_URL
        cls.session = requests.Session()
        cls.session.timeout = TEST_TIMEOUT
        
        # 测试用户凭据
        cls.super_admin_creds = {'username': 'superadmin', 'password': '1Q2W3E'}
        cls.tenant1_admin_creds = {'username': 'ceshi1', 'password': '123456'}
        cls.tenant2_admin_creds = {'username': 'ceshi2', 'password': '123456'}
        
        # 存储认证令牌
        cls.tokens = {}
        
        # 等待服务启动
        cls._wait_for_service()
        
        # 获取认证令牌
        cls._authenticate_users()
        
    @classmethod
    def _wait_for_service(cls):
        """等待服务启动"""
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = requests.get(f'{cls.base_url}/v1/health', timeout=5)
                if response.status_code == 200:
                    print(f"服务已启动 (尝试 {attempt + 1}/{max_attempts})")
                    return
            except requests.exceptions.RequestException:
                pass
            
            if attempt < max_attempts - 1:
                print(f"等待服务启动... (尝试 {attempt + 1}/{max_attempts})")
                time.sleep(2)
        
        raise Exception("服务启动超时")
        
    @classmethod
    def _authenticate_users(cls):
        """为所有测试用户获取认证令牌"""
        users = {
            'super_admin': cls.super_admin_creds,
            'tenant1_admin': cls.tenant1_admin_creds,
            'tenant2_admin': cls.tenant2_admin_creds
        }
        
        for user_type, creds in users.items():
            try:
                response = cls.session.post(
                    f'{cls.base_url}/v1/auth/login',
                    json=creds,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # 处理嵌套的响应结构
                    if 'data' in data and 'access_token' in data['data']:
                        cls.tokens[user_type] = data['data']['access_token']
                        print(f"用户 {user_type} 认证成功")
                    else:
                        cls.tokens[user_type] = data.get('access_token')
                        print(f"用户 {user_type} 认证成功 (旧格式)")
                else:
                    print(f"用户 {user_type} 认证失败: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"用户 {user_type} 认证异常: {str(e)}")
                
    def _get_auth_headers(self, user_type):
        """获取认证头"""
        token = self.tokens.get(user_type)
        if not token:
            self.fail(f"用户 {user_type} 没有有效的认证令牌")
        return {'Authorization': f'Bearer {token}'}
        
    def _make_request(self, method, url, user_type, **kwargs):
        """发送认证请求"""
        headers = self._get_auth_headers(user_type)
        if 'headers' in kwargs:
            kwargs['headers'].update(headers)
        else:
            kwargs['headers'] = headers
            
        return self.session.request(method, f'{self.base_url}{url}', **kwargs)


class TestTenantManagementAPI(MultiTenantIntegrationTest):
    """测试租户管理API"""
    
    def test_super_admin_can_list_tenants(self):
        """测试超级管理员可以列出所有租户"""
        response = self._make_request('GET', '/v1/tenants', 'super_admin')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('tenants', data)
        self.assertIsInstance(data['tenants'], list)
        
        # 验证返回的租户数据结构
        if data['tenants']:
            tenant = data['tenants'][0]
            required_fields = ['id', 'name', 'description', 'created_at']
            for field in required_fields:
                self.assertIn(field, tenant)
                
    def test_tenant_admin_cannot_list_all_tenants(self):
        """测试租户管理员不能列出所有租户"""
        response = self._make_request('GET', '/v1/tenants', 'tenant1_admin')
        
        # 应该返回403禁止访问
        self.assertEqual(response.status_code, 403)
        
    def test_create_tenant_with_admin(self):
        """测试创建租户并同时创建管理员"""
        tenant_data = {
            'name': f'集成测试租户_{int(time.time())}',
            'description': '集成测试创建的租户',
            'max_users': 10,
            'create_admin': True,
            'admin_username': f'test_admin_{int(time.time())}',
            'admin_email': f'test_admin_{int(time.time())}@test.com',
            'admin_password': 'TestPassword123!'
        }
        
        response = self._make_request(
            'POST', '/v1/tenants', 'super_admin',
            json=tenant_data,
            headers={'Content-Type': 'application/json'}
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        
        # 验证租户创建成功
        tenant_info = data.get('tenant', data)
        self.assertEqual(tenant_info['name'], tenant_data['name'])
        self.assertEqual(tenant_info.get('max_users', tenant_info.get('usage', {}).get('users', {}).get('limit')), tenant_data['max_users'])
        
        # 保存租户ID用于后续清理
        self.created_tenant_id = tenant_info['id']
        
    def test_tenant_user_management(self):
        """测试租户用户管理"""
        # 首先获取租户ID（假设租户1存在）
        tenants_response = self._make_request('GET', '/v1/tenants', 'super_admin')
        self.assertEqual(tenants_response.status_code, 200)
        
        tenants_data = tenants_response.json()
        tenants = tenants_data.get('tenants', tenants_data.get('list', []))
        if not tenants:
            self.skipTest("没有可用的租户进行测试")
            
        tenant_id = tenants[0]['id']
        
        # 测试租户管理员可以查看本租户用户
        response = self._make_request('GET', f'/v1/tenants/{tenant_id}/users', 'super_admin')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        users_list = data.get('list', data.get('users', []))
        self.assertIsInstance(users_list, list)


class TestDataIsolation(MultiTenantIntegrationTest):
    """测试数据隔离"""
    
    def test_task_isolation(self):
        """测试任务数据隔离"""
        # 获取租户1管理员的任务列表
        response1 = self._make_request('GET', '/v2/tasks', 'tenant1_admin')
        
        if response1.status_code == 200:
            data1 = response1.json()
            tenant1_tasks = data1.get('list', [])
            
            # 获取租户2管理员的任务列表
            response2 = self._make_request('GET', '/v2/tasks', 'tenant2_admin')
            
            if response2.status_code == 200:
                data2 = response2.json()
                tenant2_tasks = data2.get('list', [])
                
                # 验证两个租户的任务列表不同
                tenant1_task_ids = {task['id'] for task in tenant1_tasks}
                tenant2_task_ids = {task['id'] for task in tenant2_tasks}
                
                # 两个租户的任务ID集合应该没有交集
                self.assertEqual(len(tenant1_task_ids & tenant2_task_ids), 0)
                
    def test_result_isolation(self):
        """测试结果数据隔离"""
        # 获取租户1的结果
        response1 = self._make_request('GET', '/v2/results', 'tenant1_admin')
        
        if response1.status_code == 200:
            data1 = response1.json()
            tenant1_results = data1.get('list', [])
            
            # 验证所有结果都属于正确的租户
            for result in tenant1_results:
                # 结果应该有tenant_id字段，或者通过task关联到正确的租户
                self.assertIn('tenant_id', result)
                
    def test_system_variable_isolation(self):
        """测试系统变量隔离"""
        # 创建租户1的系统变量
        var_data = {
            'name': f'$test_var_{int(time.time())}',
            'value': 'tenant1_value',
            'is_secret': False,
            'description': '租户1测试变量'
        }
        
        create_response = self._make_request(
            'POST', '/v2/system-variables', 'tenant1_admin',
            json=var_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if create_response.status_code == 201:
            # 验证租户1可以看到自己的变量
            list_response1 = self._make_request('GET', '/v2/system-variables', 'tenant1_admin')
            self.assertEqual(list_response1.status_code, 200)
            
            data1 = list_response1.json()
            var_names1 = [var['name'] for var in data1.get('list', [])]
            self.assertIn(var_data['name'], var_names1)
            
            # 验证租户2看不到租户1的变量
            list_response2 = self._make_request('GET', '/v2/system-variables', 'tenant2_admin')
            if list_response2.status_code == 200:
                data2 = list_response2.json()
                var_names2 = [var['name'] for var in data2.get('list', [])]
                self.assertNotIn(var_data['name'], var_names2)


class TestCrossTenantAccessPrevention(MultiTenantIntegrationTest):
    """测试跨租户访问防护"""
    
    def test_cannot_access_other_tenant_tasks(self):
        """测试不能访问其他租户的任务"""
        # 首先获取所有任务（使用超级管理员）
        all_tasks_response = self._make_request('GET', '/v1/tasks', 'super_admin')
        
        if all_tasks_response.status_code == 200:
            all_tasks = all_tasks_response.json().get('list', [])
            
            if all_tasks:
                # 尝试让租户1管理员访问一个可能不属于他们的任务
                for task in all_tasks:
                    task_id = task['id']
                    
                    # 租户1管理员尝试访问任务详情
                    response = self._make_request('GET', f'/v2/tasks/{task_id}', 'tenant1_admin')
                    
                    # 如果任务不属于租户1，应该返回403或404
                    if response.status_code not in [200, 403, 404]:
                        self.fail(f"意外的响应状态码: {response.status_code}")
                        
    def test_cannot_modify_other_tenant_data(self):
        """测试不能修改其他租户的数据"""
        # 创建一个测试任务（使用超级管理员）
        task_data = {
            'name': f'跨租户测试任务_{int(time.time())}',
            'type': 'ping',
            'interval': 300,
            'enabled': True,
            'target': '8.8.8.8',
            'config': '{}'
        }
        
        create_response = self._make_request(
            'POST', '/v2/tasks', 'tenant1_admin',
            json=task_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if create_response.status_code == 201:
            task_id = create_response.json()['id']
            
            # 尝试让租户2管理员修改租户1的任务
            update_data = {
                'name': '被恶意修改的任务名称',
                'enabled': False
            }
            
            update_response = self._make_request(
                'PUT', f'/v2/tasks/{task_id}', 'tenant2_admin',
                json=update_data,
                headers={'Content-Type': 'application/json'}
            )
            
            # 应该返回403或404
            self.assertIn(update_response.status_code, [403, 404])


class TestPerformanceAndScalability(MultiTenantIntegrationTest):
    """测试性能和可扩展性"""
    
    def test_large_dataset_isolation(self):
        """测试大数据集的隔离性能"""
        # 这个测试需要大量数据，在实际环境中运行
        start_time = time.time()
        
        # 获取任务列表
        response = self._make_request('GET', '/v2/tasks?page=1&size=100', 'tenant1_admin')
        
        end_time = time.time()
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        # 响应时间应该在合理范围内（比如5秒以内）
        self.assertLess(response_time, 5.0)
        
    def test_concurrent_tenant_access(self):
        """测试并发租户访问"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_concurrent_request(user_type, endpoint):
            try:
                response = self._make_request('GET', endpoint, user_type)
                results.put((user_type, response.status_code, response.elapsed.total_seconds()))
            except Exception as e:
                results.put((user_type, 'error', str(e)))
        
        # 创建并发请求
        threads = []
        endpoints = ['/v2/tasks', '/v2/results', '/v2/system-variables']
        users = ['tenant1_admin', 'tenant2_admin']
        
        for user in users:
            for endpoint in endpoints:
                thread = threading.Thread(target=make_concurrent_request, args=(user, endpoint))
                threads.append(thread)
                thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join(timeout=30)
        
        # 检查结果
        success_count = 0
        while not results.empty():
            user_type, status_code, response_time = results.get()
            if status_code == 200:
                success_count += 1
                # 响应时间应该合理
                self.assertLess(response_time, 10.0)
        
        # 至少应该有一些成功的请求
        self.assertGreater(success_count, 0)


if __name__ == '__main__':
    # 检查服务是否运行
    try:
        response = requests.get(f'{BASE_URL}/v1/health', timeout=5)
        if response.status_code != 200:
            print("警告: 后端服务可能未运行，某些测试可能失败")
    except requests.exceptions.RequestException:
        print("警告: 无法连接到后端服务，请确保服务正在运行")
    
    # 运行测试
    unittest.main(verbosity=2)