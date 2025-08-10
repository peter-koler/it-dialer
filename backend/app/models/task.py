from app import db
from datetime import datetime


class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # ping, tcp, http, etc.
    target = db.Column(db.String(255), nullable=False)
    interval = db.Column(db.Integer, nullable=False, default=60)  # seconds
    enabled = db.Column(db.Boolean, nullable=False, default=True)
    config = db.Column(db.Text)  # JSON configuration for the task
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'target': self.target,
            'interval': self.interval,
            'enabled': self.enabled,
            'config': self.config,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Task {self.name}>'