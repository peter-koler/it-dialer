from app import db
from datetime import datetime


class Result(db.Model):
    __tablename__ = 'results'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(50), nullable=False)  # success, failed, timeout
    response_time = db.Column(db.Float)  # milliseconds
    message = db.Column(db.Text)  # error message or additional info
    details = db.Column(db.Text)  # JSON details of the result
    agent_id = db.Column(db.String(100))  # Agent ID
    agent_area = db.Column(db.String(100))  # Agent区域
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id', ondelete='CASCADE'), 
                         nullable=True, comment='租户ID')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    
    # Relationship - 添加overlaps参数以解决警告
    task = db.relationship('Task', lazy=True, overlaps="related_task,results")
    
    def to_dict(self):
        # 解析details字段为JSON对象
        details_data = None
        if self.details:
            try:
                import json
                details_data = json.loads(self.details)
            except:
                details_data = self.details
        
        return {
            'id': self.id,
            'task_id': self.task_id,
            'status': self.status,
            'response_time': self.response_time,
            'message': self.message,
            'details': details_data,
            'agent_id': self.agent_id,
            'agent_area': self.agent_area,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'task': self.task.to_dict() if self.task else None
        }
    
    def __repr__(self):
        return f'<Result {self.id}>'