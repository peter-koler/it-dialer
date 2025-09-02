from app import db
from datetime import datetime
import json


class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    step_id = db.Column(db.String(100), nullable=True)  # API任务的步骤ID
    alert_type = db.Column(db.String(50), nullable=False)  # status_code, response_time, task_status, task_timeout, assertion_failed, task_status, task_timeout
    alert_level = db.Column(db.String(20), nullable=False, default='warning')  # critical, warning, info
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, resolved, ignored
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    trigger_value = db.Column(db.String(100), nullable=True)  # 触发告警的实际值
    threshold_value = db.Column(db.String(100), nullable=True)  # 阈值
    agent_id = db.Column(db.String(100), nullable=True)  # 触发告警的节点ID
    agent_area = db.Column(db.String(100), nullable=True)  # 触发告警的节点区域
    trigger_type = db.Column(db.String(20), nullable=True)  # 触发类型(point_count/consecutive/both)
    trigger_mode = db.Column(db.String(10), nullable=True)  # 触发模式(OR/AND)
    snapshot_data = db.Column(db.Text, nullable=True)  # JSON格式的快照数据
    assigned_to = db.Column(db.String(100), nullable=True)  # 分配给的用户
    resolved_by = db.Column(db.String(100), nullable=True)  # 处理人
    resolved_at = db.Column(db.DateTime, nullable=True)  # 处理时间
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id', ondelete='CASCADE'), 
                         nullable=True, comment='租户ID')
    is_deleted = db.Column(db.Boolean, default=False, nullable=False, comment='是否已删除')
    deleted_at = db.Column(db.DateTime, nullable=True, comment='删除时间')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    task = db.relationship('Task', lazy=True)
    
    def to_dict(self):
        """转换为字典格式"""
        data = {
            'id': self.id,
            'task_id': self.task_id,
            'step_id': self.step_id,
            'alert_type': self.alert_type,
            'alert_level': self.alert_level,
            'status': self.status,
            'title': self.title,
            'content': self.content,
            'trigger_value': self.trigger_value,
            'threshold_value': self.threshold_value,
            'agent_id': self.agent_id,
            'agent_area': self.agent_area,
            'trigger_type': self.trigger_type,
            'trigger_mode': self.trigger_mode,
            'assigned_to': self.assigned_to,
            'resolved_by': self.resolved_by,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'tenant_id': self.tenant_id,
            'is_deleted': self.is_deleted,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'task_name': self.task.name if self.task else None,
            'task_type': self.task.type if self.task else 'unknown',  # 添加任务类型字段
            # 前端期望的字段名
            'taskName': self.task.name if self.task else None,
            'triggerTime': self.created_at.isoformat(),
            'level': self.alert_level  # 前端期望的告警级别字段名
        }
        
        # 解析快照数据
        snapshot_parsed = None
        if self.snapshot_data:
            try:
                snapshot_parsed = json.loads(self.snapshot_data)
            except (json.JSONDecodeError, TypeError):
                snapshot_parsed = None
        
        data['snapshot_data'] = snapshot_parsed
        data['snapshot'] = snapshot_parsed  # 前端期望的快照字段名
            
        return data
    
    def set_snapshot_data(self, data):
        """设置快照数据"""
        if data:
            self.snapshot_data = json.dumps(data, ensure_ascii=False)
        else:
            self.snapshot_data = None
    
    def get_snapshot_data(self):
        """获取快照数据"""
        if self.snapshot_data:
            try:
                return json.loads(self.snapshot_data)
            except (json.JSONDecodeError, TypeError):
                return None
        return None
    
    @staticmethod
    def get_alert_stats():
        """获取告警统计信息"""
        total = Alert.query.count()
        pending = Alert.query.filter_by(status='pending').count()
        resolved = Alert.query.filter_by(status='resolved').count()
        ignored = Alert.query.filter_by(status='ignored').count()
        
        critical = Alert.query.filter_by(alert_level='critical').count()
        warning = Alert.query.filter_by(alert_level='warning').count()
        info = Alert.query.filter_by(alert_level='info').count()
        
        return {
            'total': total,
            'pending': pending,
            'resolved': resolved,
            'ignored': ignored,
            'critical': critical,
            'warning': warning,
            'info': info
        }


class AlertConfig(db.Model):
    __tablename__ = 'alert_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    step_id = db.Column(db.String(100), nullable=True)  # API任务的步骤ID
    alert_type = db.Column(db.String(50), nullable=False)  # status_code, response_time
    enabled = db.Column(db.Boolean, nullable=False, default=True)
    config = db.Column(db.Text, nullable=False)  # JSON配置
    min_points = db.Column(db.Integer, nullable=False, default=1)  # 监测点数量阈值
    min_occurrences = db.Column(db.Integer, nullable=False, default=1)  # 连续次数阈值
    trigger_mode = db.Column(db.String(10), nullable=False, default='OR')  # 逻辑模式(OR/AND)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id', ondelete='CASCADE'), 
                         nullable=True, comment='租户ID')
    is_deleted = db.Column(db.Boolean, default=False, nullable=False, comment='是否已删除')
    deleted_at = db.Column(db.DateTime, nullable=True, comment='删除时间')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    task = db.relationship('Task', lazy=True)
    
    def to_dict(self):
        """转换为字典格式"""
        data = {
            'id': self.id,
            'task_id': self.task_id,
            'step_id': self.step_id,
            'alert_type': self.alert_type,
            'enabled': self.enabled,
            'min_points': self.min_points,
            'min_occurrences': self.min_occurrences,
            'trigger_mode': self.trigger_mode,
            'tenant_id': self.tenant_id,
            'is_deleted': self.is_deleted,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        # 解析配置数据
        if self.config:
            try:
                data['config'] = json.loads(self.config)
            except (json.JSONDecodeError, TypeError):
                data['config'] = {}
        else:
            data['config'] = {}
            
        return data
    
    def set_config(self, config_data):
        """设置配置数据"""
        if config_data:
            self.config = json.dumps(config_data, ensure_ascii=False)
        else:
            self.config = '{}'
    
    def get_config(self):
        """获取配置数据"""
        if self.config:
            try:
                return json.loads(self.config)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}