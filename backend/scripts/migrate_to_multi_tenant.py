#!/usr/bin/env python3
"""
数据迁移脚本：将现有数据迁移至多租户架构

该脚本将：
1. 创建默认租户
2. 将所有现有用户关联到默认租户
3. 将所有现有数据（任务、结果、节点等）关联到默认租户
4. 确保向后兼容性
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models.user import User
from app.models.tenant import Tenant, UserTenant
from app.models.task import Task
from app.models.result import Result
from app.models.node import Node
from app.models.system_variable import SystemVariable
from app.models.alert import Alert, AlertConfig
from datetime import datetime
import uuid


def create_default_tenant():
    """创建默认租户"""
    print("正在创建默认租户...")
    
    # 检查是否已存在默认租户
    default_tenant = Tenant.query.filter_by(name='Default Tenant').first()
    if default_tenant:
        print(f"默认租户已存在: {default_tenant.id}")
        return default_tenant
    
    # 创建默认租户
    default_tenant = Tenant(
        id=str(uuid.uuid4()),
        name='Default Tenant',
        description='系统默认租户，用于向后兼容',
        subscription_level='enterprise',  # 给默认租户最高权限
        max_tasks=1000,
        max_nodes=100,
        max_variables=500,
        max_alerts=200,
        status='active'
    )
    
    db.session.add(default_tenant)
    db.session.commit()
    
    print(f"默认租户创建成功: {default_tenant.id}")
    return default_tenant


def migrate_users_to_tenant(default_tenant):
    """将所有用户关联到默认租户"""
    print("正在迁移用户到默认租户...")
    
    users = User.query.all()
    migrated_count = 0
    
    for user in users:
        # 检查用户是否已关联到租户
        existing_relation = UserTenant.query.filter_by(
            user_id=user.id,
            tenant_id=default_tenant.id
        ).first()
        
        if not existing_relation:
            # 根据用户原有角色设置租户角色
            tenant_role = 'super_admin' if user.role == 'admin' else 'user'
            
            user_tenant = UserTenant(
                user_id=user.id,
                tenant_id=default_tenant.id,
                role=tenant_role
            )
            
            db.session.add(user_tenant)
            migrated_count += 1
    
    db.session.commit()
    print(f"用户迁移完成，共迁移 {migrated_count} 个用户")


def migrate_tasks_to_tenant(default_tenant):
    """将所有任务关联到默认租户"""
    print("正在迁移任务到默认租户...")
    
    tasks = Task.query.filter(Task.tenant_id.is_(None)).all()
    
    for task in tasks:
        task.tenant_id = default_tenant.id
    
    db.session.commit()
    print(f"任务迁移完成，共迁移 {len(tasks)} 个任务")


def migrate_results_to_tenant(default_tenant):
    """将所有结果关联到默认租户"""
    print("正在迁移结果到默认租户...")
    
    results = Result.query.filter(Result.tenant_id.is_(None)).all()
    
    for result in results:
        result.tenant_id = default_tenant.id
    
    db.session.commit()
    print(f"结果迁移完成，共迁移 {len(results)} 个结果")


def migrate_nodes_to_tenant(default_tenant):
    """将所有节点关联到默认租户"""
    print("正在迁移节点到默认租户...")
    
    nodes = Node.query.filter(Node.tenant_id.is_(None)).all()
    
    for node in nodes:
        node.tenant_id = default_tenant.id
    
    db.session.commit()
    print(f"节点迁移完成，共迁移 {len(nodes)} 个节点")


def migrate_system_variables_to_tenant(default_tenant):
    """将所有系统变量关联到默认租户"""
    print("正在迁移系统变量到默认租户...")
    
    variables = SystemVariable.query.filter(SystemVariable.tenant_id.is_(None)).all()
    
    for variable in variables:
        variable.tenant_id = default_tenant.id
    
    db.session.commit()
    print(f"系统变量迁移完成，共迁移 {len(variables)} 个变量")


def migrate_alerts_to_tenant(default_tenant):
    """将所有告警关联到默认租户"""
    print("正在迁移告警到默认租户...")
    
    # 迁移告警记录
    alerts = Alert.query.filter(Alert.tenant_id.is_(None)).all()
    for alert in alerts:
        alert.tenant_id = default_tenant.id
    
    # 迁移告警配置
    alert_configs = AlertConfig.query.filter(AlertConfig.tenant_id.is_(None)).all()
    for config in alert_configs:
        config.tenant_id = default_tenant.id
    
    db.session.commit()
    print(f"告警迁移完成，共迁移 {len(alerts)} 个告警记录和 {len(alert_configs)} 个告警配置")


def main():
    """主函数"""
    print("开始多租户数据迁移...")
    print(f"迁移时间: {datetime.now()}")
    
    app = create_app()
    
    with app.app_context():
        try:
            # 1. 创建默认租户
            default_tenant = create_default_tenant()
            
            # 2. 迁移用户
            migrate_users_to_tenant(default_tenant)
            
            # 3. 迁移各种数据
            migrate_tasks_to_tenant(default_tenant)
            migrate_results_to_tenant(default_tenant)
            migrate_nodes_to_tenant(default_tenant)
            migrate_system_variables_to_tenant(default_tenant)
            migrate_alerts_to_tenant(default_tenant)
            
            print("\n=== 迁移完成 ===")
            print(f"默认租户ID: {default_tenant.id}")
            print(f"默认租户名称: {default_tenant.name}")
            print("所有现有数据已成功迁移到多租户架构")
            
        except Exception as e:
            print(f"迁移过程中发生错误: {str(e)}")
            db.session.rollback()
            sys.exit(1)


if __name__ == '__main__':
    main()