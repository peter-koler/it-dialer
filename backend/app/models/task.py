from app import db
from datetime import datetime


class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # ping, tcp, http, api, etc.
    target = db.Column(db.String(255), nullable=False)
    interval = db.Column(db.Integer, nullable=False, default=60)  # seconds
    enabled = db.Column(db.Boolean, nullable=False, default=True)
    config = db.Column(db.Text)  # JSON configuration for the task
    agent_ids = db.Column(db.Text)  # JSON array of agent IDs
    alarm_config = db.Column(db.Text)  # JSON configuration for alarm rules
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id', ondelete='CASCADE'), 
                         nullable=True, comment='租户ID')
    status = db.Column(db.String(20), nullable=False, default='active', comment='任务状态')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    # Relationship with results (cascade delete) - 使用不同的backref名称
    results = db.relationship('Result', backref='related_task', lazy=True, cascade='all, delete-orphan')
    
    # Relationship with alerts (cascade delete)
    alerts = db.relationship('Alert', backref='related_task', lazy=True, cascade='all, delete-orphan')
    
    # Relationship with alert configs (cascade delete)
    alert_configs = db.relationship('AlertConfig', backref='related_task', lazy=True, cascade='all, delete-orphan')
    
    def get_config(self):
        """
        获取任务配置
        
        Returns:
            dict: 解析后的配置字典，如果解析失败返回None
        """
        if not self.config:
            return None
        
        try:
            import json
            return json.loads(self.config)
        except (json.JSONDecodeError, TypeError):
            return None
    
    def get_alarm_config(self):
        """
        获取告警配置
        
        Returns:
            dict: 解析后的告警配置字典，如果解析失败返回None
        """
        if not self.alarm_config:
            return None
        
        try:
            import json
            return json.loads(self.alarm_config)
        except (json.JSONDecodeError, TypeError):
            return None
    
    def to_dict(self):
        # 解析agent_ids字段为数组
        agent_ids_data = []
        if self.agent_ids:
            try:
                import json
                agent_ids_data = json.loads(self.agent_ids)
            except:
                agent_ids_data = []
        
        # 解析config字段为JSON对象
        config_data = None
        if self.config:
            try:
                import json
                config_data = json.loads(self.config)
            except:
                config_data = self.config
        
        # 解析alarm_config字段为JSON对象
        alarm_config_data = None
        if self.alarm_config:
            try:
                import json
                alarm_config_data = json.loads(self.alarm_config)
            except:
                alarm_config_data = self.alarm_config
        
        # 获取最新状态和执行统计
        from app.models.result import Result
        from sqlalchemy import func
        
        latest_result = Result.query.filter_by(task_id=self.id).order_by(Result.created_at.desc()).first()
        latest_status = latest_result.status if latest_result else None
        
        # 获取执行次数
        execution_count = Result.query.filter_by(task_id=self.id).count()
        
        # 获取平均响应时间
        avg_response_time = None
        results_with_time = Result.query.filter(
            Result.task_id == self.id,
            Result.response_time.isnot(None)
        ).all()
        
        if results_with_time:
            response_times = [r.response_time for r in results_with_time if r.response_time is not None]
            if response_times:
                avg_response_time = round(sum(response_times) / len(response_times), 2)
        
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'target': self.target,
            'interval': self.interval,
            'enabled': self.enabled,
            'config': config_data,
            'agent_ids': agent_ids_data,
            'alarm_config': alarm_config_data,
            'tenant_id': self.tenant_id,
            'status': self.status,
            'latest_status': latest_status,
            'execution_count': execution_count,
            'avg_response_time': avg_response_time,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Task {self.name}>'