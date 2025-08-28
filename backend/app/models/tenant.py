from app import db
from datetime import datetime
import uuid


class Tenant(db.Model):
    """租户模型"""
    __tablename__ = 'tenants'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment='租户ID (UUID)')
    name = db.Column(db.String(100), unique=True, nullable=False, comment='租户名称')
    description = db.Column(db.Text, comment='租户描述')
    subscription_level = db.Column(db.Enum('free', 'pro', 'enterprise', name='subscription_level_enum'), 
                                 nullable=False, default='free', comment='订阅级别')
    max_tasks = db.Column(db.Integer, nullable=False, default=10, comment='任务数量上限')
    max_nodes = db.Column(db.Integer, nullable=False, default=5, comment='节点数量上限')
    max_variables = db.Column(db.Integer, nullable=False, default=20, comment='变量数量上限')
    max_alerts = db.Column(db.Integer, nullable=False, default=10, comment='告警规则上限')
    status = db.Column(db.Enum('active', 'inactive', 'suspended', name='tenant_status_enum'), 
                      nullable=False, default='active', comment='租户状态')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, 
                          onupdate=datetime.now, comment='更新时间')
    meta_data = db.Column(db.JSON, comment='扩展字段')
    
    # 关系
    user_tenants = db.relationship('UserTenant', backref='tenant', lazy=True, cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='tenant', lazy=True, cascade='all, delete-orphan')
    results = db.relationship('Result', backref='tenant', lazy=True, cascade='all, delete-orphan')
    # 移除节点关系，节点现在是全局共享的
    # nodes = db.relationship('Node', backref='tenant', lazy=True, cascade='all, delete-orphan')
    system_variables = db.relationship('SystemVariable', backref='tenant', lazy=True, cascade='all, delete-orphan')
    alerts = db.relationship('Alert', backref='tenant', lazy=True, cascade='all, delete-orphan')
    alert_configs = db.relationship('AlertConfig', backref='tenant', lazy=True, cascade='all, delete-orphan')
    
    @classmethod
    def get_default_limits(cls, subscription_level='free'):
        """根据订阅级别获取默认限额"""
        limits = {
            'free': {
                'max_tasks': 10,
                'max_nodes': 5,
                'max_variables': 20,
                'max_alerts': 10
            },
            'pro': {
                'max_tasks': 50,
                'max_nodes': 20,
                'max_variables': 100,
                'max_alerts': 50
            },
            'enterprise': {
                'max_tasks': 200,
                'max_nodes': 100,
                'max_variables': 500,
                'max_alerts': 200
            }
        }
        return limits.get(subscription_level, limits['free'])
    
    def get_usage_stats(self):
        """获取租户资源使用统计"""
        from app.models.task import Task
        from app.models.node import Node
        from app.models.system_variable import SystemVariable
        from app.models.alert import Alert, AlertConfig
        
        # 统计当前使用量（排除软删除的记录）
        tasks_count = Task.query.filter(
            Task.tenant_id == self.id,
            Task.status != 'deleted'  # 假设有软删除状态
        ).count()
        
        # 节点现在是全局共享的，不再按租户统计
        # 为了保持兼容性，这里返回0或者总节点数的一个合理值
        nodes_count = 0  # 或者可以返回 Node.query.filter(Node.status != 'deleted').count()
        
        variables_count = SystemVariable.query.filter(
            SystemVariable.tenant_id == self.id
        ).count()
        
        alerts_count = AlertConfig.query.filter(
            AlertConfig.tenant_id == self.id
        ).count()
        
        return {
            'tasks': {'current': tasks_count, 'limit': self.max_tasks},
            'nodes': {'current': nodes_count, 'limit': self.max_nodes},
            'variables': {'current': variables_count, 'limit': self.max_variables},
            'alerts': {'current': alerts_count, 'limit': self.max_alerts}
        }
    
    def check_resource_limit(self, resource_type):
        """检查资源是否超限"""
        usage_stats = self.get_usage_stats()
        if resource_type in usage_stats:
            current = usage_stats[resource_type]['current']
            limit = usage_stats[resource_type]['limit']
            return current < limit
        return False
    
    def to_dict(self, include_usage=False):
        """转换为字典"""
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'subscription_level': self.subscription_level,
            'max_tasks': self.max_tasks,
            'max_nodes': self.max_nodes,
            'max_variables': self.max_variables,
            'max_alerts': self.max_alerts,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'meta_data': self.meta_data
        }
        
        if include_usage:
            result['usage'] = self.get_usage_stats()
        
        return result
    
    def __repr__(self):
        return f'<Tenant {self.name}>'


class UserTenant(db.Model):
    """用户-租户关联模型"""
    __tablename__ = 'user_tenants'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), 
                       primary_key=True, comment='用户ID')
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id', ondelete='CASCADE'), 
                         primary_key=True, comment='租户ID')
    role = db.Column(db.Enum('user', 'tenant_admin', 'super_admin', name='user_tenant_role_enum'), 
                    nullable=False, default='user', comment='用户在租户中的角色')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    
    # 关系
    user = db.relationship('User', backref='user_tenants', lazy=True)
    
    @classmethod
    def get_user_tenants(cls, user_id):
        """获取用户关联的所有租户"""
        return cls.query.filter_by(user_id=user_id).all()
    
    @classmethod
    def get_tenant_users(cls, tenant_id, role=None):
        """获取租户下的所有用户"""
        query = cls.query.filter_by(tenant_id=tenant_id)
        if role:
            query = query.filter_by(role=role)
        return query.all()
    
    @classmethod
    def has_permission(cls, user_id, tenant_id, required_role='user'):
        """检查用户在租户中是否有指定权限"""
        role_hierarchy = {'user': 1, 'tenant_admin': 2, 'super_admin': 3}
        required_level = role_hierarchy.get(required_role, 1)
        
        user_tenant = cls.query.filter_by(user_id=user_id, tenant_id=tenant_id).first()
        if not user_tenant:
            return False
        
        user_level = role_hierarchy.get(user_tenant.role, 0)
        return user_level >= required_level
    
    @classmethod
    def is_super_admin(cls, user_id):
        """检查用户是否为超级管理员"""
        return cls.query.filter_by(user_id=user_id, role='super_admin').first() is not None
    
    def to_dict(self):
        """转换为字典"""
        return {
            'user_id': self.user_id,
            'tenant_id': self.tenant_id,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user': self.user.to_dict() if self.user else None,
            'tenant': self.tenant.to_dict() if self.tenant else None
        }
    
    def __repr__(self):
        return f'<UserTenant user_id={self.user_id} tenant_id={self.tenant_id} role={self.role}>'