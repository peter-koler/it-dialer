from app import db
from datetime import datetime


class Alarm(db.Model):
    __tablename__ = 'alarms'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    task_name = db.Column(db.String(100), nullable=False)  # 冗余存储任务名称，便于查询
    alarm_type = db.Column(db.String(50), nullable=False)  # status, response_code, response_time, dns_ip
    level = db.Column(db.String(20), nullable=False)  # critical, warning, info
    status = db.Column(db.String(20), nullable=False, default='active')  # active, resolved
    message = db.Column(db.Text, nullable=False)  # 告警消息
    trigger_value = db.Column(db.String(255))  # 触发告警的值
    threshold_value = db.Column(db.String(255))  # 阈值
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    resolved_at = db.Column(db.DateTime)  # 解决时间
    
    # 关系
    task = db.relationship('Task', backref='alarms', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'task_name': self.task_name,
            'alarm_type': self.alarm_type,
            'level': self.level,
            'status': self.status,
            'message': self.message,
            'trigger_value': self.trigger_value,
            'threshold_value': self.threshold_value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }
    
    def resolve(self):
        """标记告警为已解决"""
        self.status = 'resolved'
        self.resolved_at = datetime.now()
    
    def __repr__(self):
        return f'<Alarm {self.id}: {self.task_name} - {self.alarm_type}>'