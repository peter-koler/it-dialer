#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试用户和租户
"""

import sys
import os
from werkzeug.security import generate_password_hash

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models.user import User
from app.models.tenant import Tenant
from app.models.tenant import UserTenant

def setup_test_data():
    """设置测试数据"""
    app = create_app()
    with app.app_context():
        # 检查超级管理员是否存在
        super_admin = User.query.filter_by(username='superadmin').first()
        if not super_admin:
            super_admin = User(
                username='superadmin',
                email='superadmin@example.com',
                password_hash=generate_password_hash('1Q2W3E'),
                role='system_admin',
                is_active=True
            )
            db.session.add(super_admin)
            print("创建超级管理员: superadmin")
        else:
            print("超级管理员已存在: superadmin")
        
        # 创建测试租户1
        tenant1 = Tenant.query.filter_by(name='测试租户1').first()
        if not tenant1:
            tenant1 = Tenant(
                name='测试租户1',
                description='第一个测试租户',
                max_users=15
            )
            db.session.add(tenant1)
            db.session.flush()  # 获取ID
            print(f"创建租户1: {tenant1.name} (ID: {tenant1.id})")
        else:
            print(f"租户1已存在: {tenant1.name} (ID: {tenant1.id})")
        
        # 创建测试租户2
        tenant2 = Tenant.query.filter_by(name='测试租户2').first()
        if not tenant2:
            tenant2 = Tenant(
                name='测试租户2',
                description='第二个测试租户',
                max_users=10
            )
            db.session.add(tenant2)
            db.session.flush()  # 获取ID
            print(f"创建租户2: {tenant2.name} (ID: {tenant2.id})")
        else:
            print(f"租户2已存在: {tenant2.name} (ID: {tenant2.id})")
        
        # 创建租户1管理员
        tenant1_admin = User.query.filter_by(username='ceshi1').first()
        if not tenant1_admin:
            tenant1_admin = User(
                username='ceshi1',
                email='ceshi1@example.com',
                password_hash=generate_password_hash('123456'),
                role='tenant_admin',
                is_active=True
            )
            db.session.add(tenant1_admin)
            db.session.flush()  # 获取ID
            print("创建租户1管理员: ceshi1")
        else:
            print("租户1管理员已存在: ceshi1")
        
        # 创建租户2管理员
        tenant2_admin = User.query.filter_by(username='ceshi2').first()
        if not tenant2_admin:
            tenant2_admin = User(
                username='ceshi2',
                email='ceshi2@example.com',
                password_hash=generate_password_hash('123456'),
                role='tenant_admin',
                is_active=True
            )
            db.session.add(tenant2_admin)
            db.session.flush()  # 获取ID
            print("创建租户2管理员: ceshi2")
        else:
            print("租户2管理员已存在: ceshi2")
        
        # 创建用户租户关联
        # 租户1管理员关联
        user_tenant1 = UserTenant.query.filter_by(
            user_id=tenant1_admin.id,
            tenant_id=tenant1.id
        ).first()
        if not user_tenant1:
            user_tenant1 = UserTenant(
                user_id=tenant1_admin.id,
                tenant_id=tenant1.id,
                role='tenant_admin'
            )
            db.session.add(user_tenant1)
            print(f"关联用户 {tenant1_admin.username} 到租户 {tenant1.name}")
        else:
            print(f"用户 {tenant1_admin.username} 已关联到租户 {tenant1.name}")
        
        # 租户2管理员关联
        user_tenant2 = UserTenant.query.filter_by(
            user_id=tenant2_admin.id,
            tenant_id=tenant2.id
        ).first()
        if not user_tenant2:
            user_tenant2 = UserTenant(
                user_id=tenant2_admin.id,
                tenant_id=tenant2.id,
                role='tenant_admin'
            )
            db.session.add(user_tenant2)
            print(f"关联用户 {tenant2_admin.username} 到租户 {tenant2.name}")
        else:
            print(f"用户 {tenant2_admin.username} 已关联到租户 {tenant2.name}")
        
        # 提交所有更改
        db.session.commit()
        print("\n测试数据设置完成！")
        
        # 显示创建的数据
        print("\n=== 用户列表 ===")
        users = User.query.all()
        for user in users:
            print(f"- {user.username} (角色: {user.role}, 邮箱: {user.email})")
        
        print("\n=== 租户列表 ===")
        tenants = Tenant.query.all()
        for tenant in tenants:
            print(f"- {tenant.name} (ID: {tenant.id}, 最大用户数: {tenant.max_users})")
        
        print("\n=== 用户租户关联 ===")
        user_tenants = UserTenant.query.all()
        for ut in user_tenants:
            user = User.query.get(ut.user_id)
            tenant = Tenant.query.get(ut.tenant_id)
            print(f"- {user.username} -> {tenant.name} (角色: {ut.role})")

if __name__ == '__main__':
    setup_test_data()