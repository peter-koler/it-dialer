#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建Super Admin用户脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app import create_app, db
from app.models.user import User
from app.models.tenant import Tenant, UserTenant

def create_superadmin():
    """创建Super Admin用户"""
    app = create_app()
    
    with app.app_context():
        # 检查用户是否已存在
        existing_user = User.query.filter_by(username='superadmin').first()
        if existing_user:
            print(f"用户 'superadmin' 已存在，ID: {existing_user.id}")
            return existing_user
        
        # 创建新用户
        user = User(
            username='superadmin',
            email='superadmin@example.com',
            role='admin',  # 基础角色设为admin
            status=1
        )
        
        # 设置密码
        user.set_password('1Q2W3E')
        
        # 保存用户到数据库
        db.session.add(user)
        db.session.commit()
        
        print(f"用户 'superadmin' 创建成功，ID: {user.id}")
        
        # 检查是否存在默认租户
        default_tenant = Tenant.query.filter_by(name='Default Tenant').first()
        if not default_tenant:
            print("未找到默认租户，请先运行多租户迁移脚本")
            return user
        
        # 检查用户是否已有租户关联
        existing_user_tenant = UserTenant.query.filter_by(
            user_id=user.id, 
            tenant_id=default_tenant.id
        ).first()
        
        if existing_user_tenant:
            print(f"用户已关联到默认租户，角色: {existing_user_tenant.role}")
            # 如果不是super_admin，则更新角色
            if existing_user_tenant.role != 'super_admin':
                existing_user_tenant.role = 'super_admin'
                db.session.commit()
                print("用户角色已更新为 super_admin")
        else:
            # 创建用户租户关联，设置为super_admin角色
            user_tenant = UserTenant(
                user_id=user.id,
                tenant_id=default_tenant.id,
                role='super_admin'
            )
            
            db.session.add(user_tenant)
            db.session.commit()
            
            print(f"用户已关联到默认租户，角色: super_admin")
        
        print("\n=== Super Admin用户创建完成 ===")
        print(f"用户名: superadmin")
        print(f"密码: 1Q2W3E")
        print(f"角色: super_admin")
        print(f"邮箱: superadmin@example.com")
        print("================================")
        
        return user

if __name__ == '__main__':
    create_superadmin()