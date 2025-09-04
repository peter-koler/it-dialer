from app import db
from datetime import datetime


class Node(db.Model):
    """节点模型"""
    __tablename__ = 'nodes'
    
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.String(100), unique=True, nullable=False, comment='Agent ID')
    agent_area = db.Column(db.String(100), nullable=False, comment='Agent区域')
    ip_address = db.Column(db.String(50), nullable=False, comment='IP地址')
    hostname = db.Column(db.String(100), nullable=False, comment='主机名')
    status = db.Column(db.String(20), default='offline', comment='节点状态: online, offline, timeout, deleted')
    # 移除租户绑定，节点现在是全局共享的
    # tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id', ondelete='CASCADE'), 
    #                      nullable=True, comment='租户ID')
    last_heartbeat = db.Column(db.DateTime, comment='最后心跳时间')
    
    # 线程池状态字段
    max_workers = db.Column(db.Integer, comment='最大工作线程数')
    active_threads = db.Column(db.Integer, comment='活跃线程数')
    completed_tasks = db.Column(db.Integer, comment='已完成任务数')
    pending_tasks = db.Column(db.Integer, comment='等待任务数')
    
    # 任务状态统计字段
    total_tasks = db.Column(db.Integer, comment='总任务数')
    running_tasks = db.Column(db.Integer, comment='运行中任务数')
    failed_tasks = db.Column(db.Integer, comment='失败任务数')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def __init__(self, agent_id, agent_area, ip_address, hostname, status='offline', last_heartbeat=None):
        self.agent_id = agent_id
        self.agent_area = agent_area
        self.ip_address = ip_address
        self.hostname = hostname
        self.status = status
        self.last_heartbeat = last_heartbeat
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self):
        """将节点对象转换为字典"""
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'agent_area': self.agent_area,
            'ip_address': self.ip_address,
            'hostname': self.hostname,
            'status': self.status,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            # 线程池状态信息
            'thread_pool': {
                'max_workers': self.max_workers,
                'active_threads': self.active_threads,
                'completed_tasks': self.completed_tasks,
                'pending_tasks': self.pending_tasks
            },
            # 任务状态统计
            'task_status': {
                'total_tasks': self.total_tasks,
                'running_tasks': self.running_tasks,
                'failed_tasks': self.failed_tasks
            }
        }
    
    def __repr__(self):
        return f'<Node {self.agent_id}>'