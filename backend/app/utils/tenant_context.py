from flask import g
from functools import wraps
from sqlalchemy import and_


class TenantContext:
    """租户上下文管理器"""
    
    @staticmethod
    def get_current_tenant_id():
        """获取当前租户ID"""
        return getattr(g, 'tenant_id', None)
    
    @staticmethod
    def get_current_tenant():
        """获取当前租户对象"""
        return getattr(g, 'current_tenant', None)
    
    @staticmethod
    def get_tenant_role():
        """获取当前用户在租户中的角色"""
        return getattr(g, 'tenant_role', 'user')
    
    @staticmethod
    def is_super_admin():
        """检查当前用户是否为超级管理员"""
        return getattr(g, 'tenant_role', 'user') == 'super_admin'
    
    @staticmethod
    def is_tenant_admin():
        """检查当前用户是否为租户管理员"""
        tenant_role = getattr(g, 'tenant_role', 'user')
        return tenant_role in ['tenant_admin', 'super_admin']
    
    @staticmethod
    def filter_by_tenant(query, model_class, tenant_field='tenant_id'):
        """为查询添加租户过滤条件"""
        tenant_id = TenantContext.get_current_tenant_id()
        if tenant_id and hasattr(model_class, tenant_field):
            return query.filter(getattr(model_class, tenant_field) == tenant_id)
        return query
    
    @staticmethod
    def add_tenant_id(data, tenant_field='tenant_id'):
        """为数据添加租户ID"""
        tenant_id = TenantContext.get_current_tenant_id()
        if tenant_id:
            data[tenant_field] = tenant_id
        return data


def tenant_required(f):
    """租户权限装饰器 - 确保用户有租户上下文"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not TenantContext.get_current_tenant_id():
            from flask import jsonify
            return jsonify({
                'code': 403,
                'data': {},
                'message': '缺少租户上下文'
            }), 403
        return f(*args, **kwargs)
    return decorated


def tenant_admin_required(f):
    """租户管理员权限装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not TenantContext.is_tenant_admin():
            from flask import jsonify
            return jsonify({
                'code': 403,
                'data': {},
                'message': '需要租户管理员权限'
            }), 403
        return f(*args, **kwargs)
    return decorated


def super_admin_required(f):
    """超级管理员权限装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not TenantContext.is_super_admin():
            from flask import jsonify
            return jsonify({
                'code': 403,
                'data': {},
                'message': '需要超级管理员权限'
            }), 403
        return f(*args, **kwargs)
    return decorated


def check_resource_limit(resource_type):
    """资源限额检查装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            tenant = TenantContext.get_current_tenant()
            if tenant and not tenant.check_resource_limit(resource_type):
                from flask import jsonify
                return jsonify({
                    'code': 403,
                    'data': {},
                    'message': f'{resource_type}数量已达到限额'
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


# 便捷函数，直接调用TenantContext的方法
def get_current_tenant_id():
    """获取当前租户ID"""
    return TenantContext.get_current_tenant_id()


def get_current_tenant():
    """获取当前租户对象"""
    return TenantContext.get_current_tenant()


def filter_by_tenant(query, model_class=None, tenant_field='tenant_id'):
    """为查询添加租户过滤条件"""
    tenant_id = get_current_tenant_id()
    if tenant_id:
        if model_class:
            return TenantContext.filter_by_tenant(query, model_class, tenant_field)
        else:
            # 如果没有指定model_class，尝试从query中推断
            return query.filter(getattr(query.column_descriptions[0]['type'], tenant_field) == tenant_id)
    return query


def add_tenant_id(obj, tenant_field='tenant_id'):
    """为对象添加租户ID"""
    tenant_id = get_current_tenant_id()
    if tenant_id:
        setattr(obj, tenant_field, tenant_id)
    return obj