from app import db
from datetime import datetime
import re


class SystemVariable(db.Model):
    """系统变量模型"""
    __tablename__ = 'system_variables'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, comment='变量名')  # 变量名，格式为 $xxx
    value = db.Column(db.Text, nullable=False, comment='变量值')  # 变量值
    description = db.Column(db.Text, comment='变量描述')  # 变量描述
    is_secret = db.Column(db.Boolean, default=False, comment='是否为敏感信息')  # 是否为密钥变量
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id', ondelete='CASCADE'), 
                         nullable=True, comment='租户ID')
    is_deleted = db.Column(db.Boolean, default=False, nullable=False, comment='是否已删除')
    deleted_at = db.Column(db.DateTime, nullable=True, comment='删除时间')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 添加复合唯一索引，确保在同一租户内变量名唯一
    __table_args__ = (
        db.UniqueConstraint('name', 'tenant_id', name='uq_system_variable_name_tenant'),
    )
    
    @staticmethod
    def validate_name(name):
        """验证变量名格式是否正确（必须以$开头，后跟字母、数字或下划线）"""
        if not name:
            return False
        return bool(re.match(r'^\$[a-zA-Z][a-zA-Z0-9_]*$', name))
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'value': self.value if not self.is_secret else '***',  # 敏感信息不返回真实值
            'description': self.description,
            'is_secret': self.is_secret,
            'tenant_id': self.tenant_id,
            'is_deleted': self.is_deleted,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<SystemVariable {self.name}>'