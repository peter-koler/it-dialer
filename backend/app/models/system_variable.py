from app import db
from datetime import datetime
import re


class SystemVariable(db.Model):
    __tablename__ = 'system_variables'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # 变量名，格式为 $xxx
    value = db.Column(db.Text, nullable=False)  # 变量值
    description = db.Column(db.Text)  # 变量描述
    is_secret = db.Column(db.Boolean, default=False)  # 是否为密钥变量
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def validate_name(name):
        """验证变量名格式是否正确（必须以$开头，后跟字母、数字或下划线）"""
        if not name:
            return False
        return bool(re.match(r'^\$[a-zA-Z][a-zA-Z0-9_]*$', name))
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'value': self.value,
            'description': self.description,
            'is_secret': self.is_secret,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<SystemVariable {self.name}>'