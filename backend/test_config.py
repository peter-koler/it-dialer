#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试配置文件
为多租户功能测试提供配置支持
"""

import os
import tempfile
from app.config import Config


class TestConfig(Config):
    """测试环境配置"""
    
    # 测试标识
    TESTING = True
    
    # 使用内存数据库进行测试
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # 禁用CSRF保护（测试环境）
    WTF_CSRF_ENABLED = False
    
    # 简化密码哈希（提高测试速度）
    BCRYPT_LOG_ROUNDS = 4
    
    # JWT配置
    JWT_SECRET_KEY = 'test-jwt-secret-key-for-multitenant-testing'
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1小时
    
    # 禁用邮件发送
    MAIL_SUPPRESS_SEND = True
    
    # 日志配置
    LOG_LEVEL = 'DEBUG'
    
    # 多租户测试配置
    DEFAULT_TENANT_MAX_USERS = 15
    ENABLE_TENANT_ISOLATION = True
    
    # 测试数据配置
    TEST_SUPER_ADMIN = {
        'username': 'test_superadmin',
        'email': 'superadmin@test.com',
        'password': 'TestSuperAdmin123!'
    }
    
    TEST_TENANTS = [
        {
            'name': '测试租户1',
            'description': '第一个测试租户',
            'max_users': 10,
            'admin': {
                'username': 'tenant1_admin',
                'email': 'admin1@test.com',
                'password': 'TenantAdmin123!'
            }
        },
        {
            'name': '测试租户2',
            'description': '第二个测试租户',
            'max_users': 15,
            'admin': {
                'username': 'tenant2_admin',
                'email': 'admin2@test.com',
                'password': 'TenantAdmin123!'
            }
        }
    ]
    
    # 测试用户配置
    TEST_USERS = [
        {
            'username': 'tenant1_user1',
            'email': 'user1@tenant1.com',
            'password': 'User123!',
            'tenant': '测试租户1',
            'role': 'user'
        },
        {
            'username': 'tenant1_user2',
            'email': 'user2@tenant1.com',
            'password': 'User123!',
            'tenant': '测试租户1',
            'role': 'user'
        },
        {
            'username': 'tenant2_user1',
            'email': 'user1@tenant2.com',
            'password': 'User123!',
            'tenant': '测试租户2',
            'role': 'user'
        }
    ]


class IntegrationTestConfig(Config):
    """集成测试配置（使用真实数据库）"""
    
    # 测试标识
    TESTING = True
    
    # 使用临时SQLite文件数据库
    _db_fd, _db_path = tempfile.mkstemp(suffix='.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{_db_path}'
    
    # 测试完成后清理数据库文件
    @classmethod
    def cleanup(cls):
        """清理测试数据库文件"""
        if hasattr(cls, '_db_path') and os.path.exists(cls._db_path):
            os.unlink(cls._db_path)
        if hasattr(cls, '_db_fd'):
            os.close(cls._db_fd)
    
    # 其他配置继承自TestConfig
    BCRYPT_LOG_ROUNDS = 4
    JWT_SECRET_KEY = 'integration-test-jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    MAIL_SUPPRESS_SEND = True
    LOG_LEVEL = 'INFO'
    
    # 集成测试特定配置
    API_BASE_URL = 'http://localhost:5000/api'
    FRONTEND_BASE_URL = 'http://localhost:8080'
    
    # 测试超时配置
    REQUEST_TIMEOUT = 30
    TEST_TIMEOUT = 300  # 5分钟
    
    # 并发测试配置
    MAX_CONCURRENT_REQUESTS = 10
    
    # 性能测试配置
    PERFORMANCE_TEST_ENABLED = True
    MAX_RESPONSE_TIME = 5.0  # 5秒
    
    # 数据量测试配置
    LARGE_DATASET_SIZE = 1000
    BULK_OPERATION_SIZE = 100


class LoadTestConfig(IntegrationTestConfig):
    """负载测试配置"""
    
    # 负载测试特定配置
    LOAD_TEST_ENABLED = True
    CONCURRENT_USERS = 50
    TEST_DURATION = 300  # 5分钟
    RAMP_UP_TIME = 60   # 1分钟
    
    # 性能指标阈值
    MAX_RESPONSE_TIME = 2.0  # 2秒
    MIN_SUCCESS_RATE = 0.95  # 95%成功率
    MAX_ERROR_RATE = 0.05    # 5%错误率
    
    # 资源使用限制
    MAX_MEMORY_USAGE = 512 * 1024 * 1024  # 512MB
    MAX_CPU_USAGE = 80  # 80%


# 配置映射
config_map = {
    'testing': TestConfig,
    'integration': IntegrationTestConfig,
    'load': LoadTestConfig
}


def get_test_config(config_name='testing'):
    """获取测试配置"""
    return config_map.get(config_name, TestConfig)