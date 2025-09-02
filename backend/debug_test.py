#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app, db
from app.models.user import User
from app.models.tenant import Tenant, UserTenant
from app.models.task import Task

app = create_app()
with app.app_context():
    print(f"数据库URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # 删除并重新创建所有表
    db.drop_all()
    db.create_all()
    
    # 创建测试租户
    tenant1 = Tenant(
        name='测试租户1',
        description='测试租户1描述',
        max_users=15,
        status='active'
    )
    tenant2 = Tenant(
        name='测试租户2', 
        description='测试租户2描述',
        max_users=15,
        status='active'
    )
    
    db.session.add(tenant1)
    db.session.add(tenant2)
    db.session.commit()
    
    print(f"创建租户: {tenant1.name} (ID: {tenant1.id})")
    print(f"创建租户: {tenant2.name} (ID: {tenant2.id})")
    
    # 创建测试用户
    tenant1_admin = User(
        username='tenant1_admin',
        email='tenant1_admin@test.com',
        role='user',
        status=1
    )
    tenant1_admin.set_password('password123')
    
    db.session.add(tenant1_admin)
    db.session.commit()
    
    print(f"创建用户: {tenant1_admin.username} (ID: {tenant1_admin.id})")
    
    # 创建用户租户关联
    user_tenant1_admin = UserTenant(
        user_id=tenant1_admin.id,
        tenant_id=tenant1.id,
        role='tenant_admin'
    )
    
    db.session.add(user_tenant1_admin)
    db.session.commit()
    
    print(f"创建用户租户关联: 用户{tenant1_admin.id} -> 租户{tenant1.id}")
    
    # 创建测试任务
    task1 = Task(
        name='租户1任务',
        type='ping',
        interval=60,
        enabled=True,
        tenant_id=tenant1.id,
        target='192.168.1.1',
        config='{}'
    )
    
    db.session.add(task1)
    db.session.commit()
    
    print(f"创建任务: {task1.name} (ID: {task1.id}, 租户ID: {task1.tenant_id})")
    
    # 验证数据
    tasks = Task.query.all()
    tenants = Tenant.query.all()
    users = User.query.all()
    user_tenants = UserTenant.query.all()
    
    print(f"\n验证结果:")
    print(f"总任务数: {len(tasks)}")
    print(f"总租户数: {len(tenants)}")
    print(f"总用户数: {len(users)}")
    print(f"总用户租户关联数: {len(user_tenants)}")
    
    for task in tasks:
        print(f"任务: {task.name}, 租户ID: {task.tenant_id}")
    for tenant in tenants:
        print(f"租户: {tenant.name}, ID: {tenant.id}")
    for user in users:
        print(f"用户: {user.username}, ID: {user.id}")
    for ut in user_tenants:
        print(f"用户租户关联: 用户{ut.user_id} -> 租户{ut.tenant_id}, 角色: {ut.role}")