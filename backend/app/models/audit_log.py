# -*- coding: utf-8 -*-
"""
审计日志模型
记录系统中的重要操作，特别是多租户相关的操作
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app import db


class AuditLog(db.Model):
    """审计日志模型
    
    记录系统中的重要操作，包括：
    - 用户管理操作（创建、删除、角色变更等）
    - 租户管理操作（创建、更新、删除等）
    - 权限变更操作
    - 系统配置变更
    """
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)  # 操作者，可能为空（系统操作）
    target_user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)  # 被操作的用户
    action = Column(String(50), nullable=False, index=True)  # 操作类型
    resource_type = Column(String(50), nullable=False, index=True)  # 资源类型
    resource_id = Column(String(50), nullable=True, index=True)  # 资源ID
    details = Column(Text, nullable=True)  # 操作详情（JSON格式）
    ip_address = Column(String(45), nullable=True)  # 操作者IP地址
    user_agent = Column(String(500), nullable=True)  # 用户代理
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # 关联关系
    tenant = relationship('Tenant', backref='audit_logs')
    operator = relationship('User', foreign_keys=[user_id], backref='operated_logs')
    target_user = relationship('User', foreign_keys=[target_user_id], backref='target_logs')
    
    def __repr__(self):
        return f'<AuditLog {self.id}: {self.action} on {self.resource_type}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'user_id': self.user_id,
            'target_user_id': self.target_user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'operator_name': self.operator.username if self.operator else None,
            'target_user_name': self.target_user.username if self.target_user else None
        }
    
    @classmethod
    def log_action(cls, tenant_id, action, resource_type, user_id=None, target_user_id=None, 
                   resource_id=None, details=None, ip_address=None, user_agent=None):
        """记录操作日志
        
        Args:
            tenant_id: 租户ID
            action: 操作类型（如：create_user, delete_user, update_role等）
            resource_type: 资源类型（如：user, tenant, role等）
            user_id: 操作者用户ID
            target_user_id: 被操作的用户ID
            resource_id: 资源ID
            details: 操作详情
            ip_address: IP地址
            user_agent: 用户代理
        """
        log_entry = cls(
            tenant_id=tenant_id,
            user_id=user_id,
            target_user_id=target_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.session.add(log_entry)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # 审计日志记录失败不应该影响主要业务流程
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to log audit action: {str(e)}")
    
    @classmethod
    def get_user_logs(cls, tenant_id, user_id=None, limit=100):
        """获取用户相关的审计日志
        
        Args:
            tenant_id: 租户ID
            user_id: 用户ID，如果为None则获取所有用户的日志
            limit: 返回记录数限制
        """
        query = cls.query.filter_by(tenant_id=tenant_id)
        
        if user_id:
            query = query.filter(
                (cls.user_id == user_id) | (cls.target_user_id == user_id)
            )
        
        return query.order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_tenant_logs(cls, tenant_id, limit=100):
        """获取租户的审计日志
        
        Args:
            tenant_id: 租户ID
            limit: 返回记录数限制
        """
        return cls.query.filter_by(tenant_id=tenant_id).order_by(
            cls.created_at.desc()
        ).limit(limit).all()


# 常用的操作类型常量
class AuditAction:
    """审计操作类型常量"""
    # 用户管理
    CREATE_USER = 'create_user'
    UPDATE_USER = 'update_user'
    DELETE_USER = 'delete_user'
    ACTIVATE_USER = 'activate_user'
    DEACTIVATE_USER = 'deactivate_user'
    RESET_PASSWORD = 'reset_password'
    
    # 租户管理
    CREATE_TENANT = 'create_tenant'
    UPDATE_TENANT = 'update_tenant'
    DELETE_TENANT = 'delete_tenant'
    
    # 用户租户关联
    ADD_USER_TO_TENANT = 'add_user_to_tenant'
    REMOVE_USER_FROM_TENANT = 'remove_user_from_tenant'
    UPDATE_USER_ROLE = 'update_user_role'
    
    # 系统配置
    UPDATE_SYSTEM_CONFIG = 'update_system_config'
    
    # 登录相关
    LOGIN_SUCCESS = 'login_success'
    LOGIN_FAILED = 'login_failed'
    LOGOUT = 'logout'


# 资源类型常量
class ResourceType:
    """资源类型常量"""
    USER = 'user'
    TENANT = 'tenant'
    USER_TENANT = 'user_tenant'
    SYSTEM_CONFIG = 'system_config'
    TASK = 'task'
    NODE = 'node'
    ALERT = 'alert'