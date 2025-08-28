from app.models.tenant import Tenant
from app.models.task import Task
from app.models.node import Node
from app.models.system_variable import SystemVariable
from app.models.alert import AlertConfig
from flask import jsonify
from functools import wraps


class QuotaChecker:
    """资源配额检查器"""
    
    @staticmethod
    def check_task_quota(tenant_id):
        """检查任务配额"""
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return False, "租户不存在"
        
        # 统计当前任务数量（排除已删除的）
        current_count = Task.query.filter(
            Task.tenant_id == tenant_id,
            Task.status != 'deleted'
        ).count()
        
        if current_count >= tenant.max_tasks:
            return False, f"任务数量已达上限 ({current_count}/{tenant.max_tasks})"
        
        return True, f"当前任务数量: {current_count}/{tenant.max_tasks}"
    
    @staticmethod
    def check_node_quota(tenant_id):
        """检查节点配额 - 节点现在是全局共享的，不再绑定到特定租户"""
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return False, "租户不存在"
        
        # 节点现在是全局共享的，统计所有活跃节点数量
        current_count = Node.query.filter(
            Node.status != 'deleted'
        ).count()
        
        # 由于节点是全局共享的，这里返回总节点数作为参考
        return True, f"全局节点数量: {current_count} (节点现已全局共享)"
    
    @staticmethod
    def check_variable_quota(tenant_id):
        """检查系统变量配额"""
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return False, "租户不存在"
        
        # 统计当前变量数量
        current_count = SystemVariable.query.filter(
            SystemVariable.tenant_id == tenant_id
        ).count()
        
        if current_count >= tenant.max_variables:
            return False, f"系统变量数量已达上限 ({current_count}/{tenant.max_variables})"
        
        return True, f"当前变量数量: {current_count}/{tenant.max_variables}"
    
    @staticmethod
    def check_alert_quota(tenant_id):
        """检查告警规则配额"""
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return False, "租户不存在"
        
        # 统计当前告警规则数量
        current_count = AlertConfig.query.filter(
            AlertConfig.tenant_id == tenant_id
        ).count()
        
        if current_count >= tenant.max_alerts:
            return False, f"告警规则数量已达上限 ({current_count}/{tenant.max_alerts})"
        
        return True, f"当前告警规则数量: {current_count}/{tenant.max_alerts}"
    
    @staticmethod
    def get_quota_info(tenant_id):
        """获取租户所有配额信息"""
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return None
        
        return {
            'tasks': {
                'current': Task.query.filter(
                    Task.tenant_id == tenant_id,
                    Task.status != 'deleted'
                ).count(),
                'limit': tenant.max_tasks
            },
            'nodes': {
                'current': Node.query.filter(
                    Node.status != 'deleted'
                ).count(),
                'limit': tenant.max_nodes,
                'note': '节点现已全局共享，此处显示全局节点总数'
            },
            'variables': {
                'current': SystemVariable.query.filter(
                    SystemVariable.tenant_id == tenant_id
                ).count(),
                'limit': tenant.max_variables
            },
            'alerts': {
                'current': AlertConfig.query.filter(
                    AlertConfig.tenant_id == tenant_id
                ).count(),
                'limit': tenant.max_alerts
            }
        }


def require_quota(resource_type):
    """装饰器：检查资源配额"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 从请求中获取租户ID
            tenant_id = getattr(request, 'tenant_id', None)
            if not tenant_id:
                return jsonify({'error': '未找到租户信息'}), 400
            
            # 根据资源类型检查配额
            checker_map = {
                'task': QuotaChecker.check_task_quota,
                'node': QuotaChecker.check_node_quota,
                'variable': QuotaChecker.check_variable_quota,
                'alert': QuotaChecker.check_alert_quota
            }
            
            checker = checker_map.get(resource_type)
            if not checker:
                return jsonify({'error': f'未知的资源类型: {resource_type}'}), 400
            
            is_allowed, message = checker(tenant_id)
            if not is_allowed:
                return jsonify({
                    'error': '资源配额不足',
                    'message': message,
                    'resource_type': resource_type
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


class SoftDeleteMixin:
    """软删除混入类"""
    
    @classmethod
    def soft_delete(cls, record_id, tenant_id=None):
        """软删除记录"""
        query = cls.query.filter_by(id=record_id)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        
        record = query.first()
        if not record:
            return False, "记录不存在"
        
        # 检查是否有status字段
        if hasattr(record, 'status'):
            record.status = 'deleted'
        else:
            # 如果没有status字段，添加deleted_at字段
            if hasattr(record, 'deleted_at'):
                from datetime import datetime
                record.deleted_at = datetime.now()
        
        try:
            from app import db
            db.session.commit()
            return True, "删除成功"
        except Exception as e:
            db.session.rollback()
            return False, f"删除失败: {str(e)}"
    
    @classmethod
    def restore(cls, record_id, tenant_id=None):
        """恢复软删除的记录"""
        query = cls.query.filter_by(id=record_id)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        
        record = query.first()
        if not record:
            return False, "记录不存在"
        
        # 恢复记录
        if hasattr(record, 'status') and record.status == 'deleted':
            record.status = 'active'  # 或其他适当的状态
        elif hasattr(record, 'deleted_at'):
            record.deleted_at = None
        
        try:
            from app import db
            db.session.commit()
            return True, "恢复成功"
        except Exception as e:
            db.session.rollback()
            return False, f"恢复失败: {str(e)}"
    
    @classmethod
    def get_active_records(cls, tenant_id=None):
        """获取未删除的记录"""
        query = cls.query
        
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        
        # 过滤掉已删除的记录
        if hasattr(cls, 'status'):
            query = query.filter(cls.status != 'deleted')
        elif hasattr(cls, 'deleted_at'):
            query = query.filter(cls.deleted_at.is_(None))
        
        return query


def add_quota_info_to_response(response_data, tenant_id):
    """在响应中添加配额信息"""
    quota_info = QuotaChecker.get_quota_info(tenant_id)
    if quota_info:
        if isinstance(response_data, dict):
            response_data['quota_info'] = quota_info
        elif isinstance(response_data, list):
            # 如果是列表响应，包装成字典
            response_data = {
                'data': response_data,
                'quota_info': quota_info
            }
    return response_data