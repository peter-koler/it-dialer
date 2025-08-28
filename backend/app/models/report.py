from app import db
from datetime import datetime
import json


class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # tcp/ping/http/api
    task_ids = db.Column(db.Text)  # JSON array of task IDs
    time_range = db.Column(db.Text)  # JSON time range configuration
    metrics = db.Column(db.Text)  # JSON metrics collection
    generate_time = db.Column(db.DateTime, nullable=False, default=datetime.now)
    file_path = db.Column(db.String(500))  # Export file path
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    def get_task_ids(self):
        """
        获取任务ID列表
        
        Returns:
            list: 解析后的任务ID列表，如果解析失败返回空列表
        """
        if not self.task_ids:
            return []
        
        try:
            return json.loads(self.task_ids)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_task_ids(self, task_ids):
        """
        设置任务ID列表
        
        Args:
            task_ids (list): 任务ID列表
        """
        self.task_ids = json.dumps(task_ids)
    
    def get_time_range(self):
        """
        获取时间范围配置
        
        Returns:
            dict: 解析后的时间范围配置，如果解析失败返回None
        """
        if not self.time_range:
            return None
        
        try:
            return json.loads(self.time_range)
        except (json.JSONDecodeError, TypeError):
            return None
    
    def set_time_range(self, time_range):
        """
        设置时间范围配置
        
        Args:
            time_range (dict): 时间范围配置
        """
        self.time_range = json.dumps(time_range)
    
    def get_metrics(self):
        """
        获取指标集合
        
        Returns:
            dict: 解析后的指标集合，如果解析失败返回None
        """
        if not self.metrics:
            return None
        
        try:
            return json.loads(self.metrics)
        except (json.JSONDecodeError, TypeError):
            return None
    
    def set_metrics(self, metrics):
        """
        设置指标集合
        
        Args:
            metrics (dict): 指标集合
        """
        self.metrics = json.dumps(metrics)
    
    def to_dict(self):
        """
        转换为字典格式
        
        Returns:
            dict: 报表信息字典
        """
        return {
            'id': self.id,
            'type': self.type,
            'task_ids': self.get_task_ids(),
            'time_range': self.get_time_range(),
            'metrics': self.get_metrics(),
            'generate_time': self.generate_time.isoformat() if self.generate_time else None,
            'file_path': self.file_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Report {self.id} - {self.type}>'


class ReportSubscription(db.Model):
    __tablename__ = 'report_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # tcp/ping/http/api
    task_ids = db.Column(db.Text)  # JSON array of task IDs
    period = db.Column(db.String(20), nullable=False)  # daily/weekly/monthly
    target = db.Column(db.Text)  # JSON push target configuration
    enabled = db.Column(db.Boolean, nullable=False, default=True)
    last_sent = db.Column(db.DateTime)  # Last sent time
    create_time = db.Column(db.DateTime, nullable=False, default=datetime.now)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    def get_task_ids(self):
        """
        获取任务ID列表
        
        Returns:
            list: 解析后的任务ID列表，如果解析失败返回空列表
        """
        if not self.task_ids:
            return []
        
        try:
            return json.loads(self.task_ids)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_task_ids(self, task_ids):
        """
        设置任务ID列表
        
        Args:
            task_ids (list): 任务ID列表
        """
        self.task_ids = json.dumps(task_ids)
    
    def get_target(self):
        """
        获取推送目标配置
        
        Returns:
            dict: 解析后的推送目标配置，如果解析失败返回None
        """
        if not self.target:
            return None
        
        try:
            return json.loads(self.target)
        except (json.JSONDecodeError, TypeError):
            return None
    
    def set_target(self, target):
        """
        设置推送目标配置
        
        Args:
            target (dict): 推送目标配置
        """
        self.target = json.dumps(target)
    
    def to_dict(self):
        """
        转换为字典格式
        
        Returns:
            dict: 订阅信息字典
        """
        return {
            'id': self.id,
            'type': self.type,
            'task_ids': self.get_task_ids(),
            'period': self.period,
            'target': self.get_target(),
            'enabled': self.enabled,
            'last_sent': self.last_sent.isoformat() if self.last_sent else None,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<ReportSubscription {self.id} - {self.type} - {self.period}>'