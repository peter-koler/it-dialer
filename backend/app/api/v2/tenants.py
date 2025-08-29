from flask import request, jsonify
from . import v2_bp as bp
from app.models.tenant import Tenant
from app.utils.auth_decorators import token_required
from app.utils.tenant_context import super_admin_required


@bp.route('/tenants/<tenant_id>/usage', methods=['GET'])
@token_required
def get_tenant_usage(tenant_id):
    """获取租户资源使用统计 (v2版本)"""
    try:
        from app.utils.tenant_context import TenantContext
        from flask import g
        
        # 权限检查：超级管理员可以查看所有租户，普通用户只能查看自己的租户
        current_tenant_id = TenantContext.get_current_tenant_id()
        is_super_admin = TenantContext.is_super_admin()
        
        if not is_super_admin and current_tenant_id != tenant_id:
            return jsonify({
                'code': 403,
                'data': {},
                'message': '无权限访问该租户的使用统计'
            }), 403
        
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return jsonify({
                'code': 404,
                'data': {},
                'message': '租户不存在'
            }), 404
        
        # 获取使用统计
        usage_stats = tenant.get_usage_stats()
        
        # 计算使用率
        for resource_type, stats in usage_stats.items():
            if stats['limit'] > 0:
                stats['usage_rate'] = round((stats['current'] / stats['limit']) * 100, 2)
            else:
                stats['usage_rate'] = 0
        
        return jsonify({
            'code': 0,
            'data': {
                'tenant_id': tenant.id,
                'tenant_name': tenant.name,
                'subscription_level': tenant.subscription_level,
                'usage_stats': usage_stats,
                'last_updated': tenant.updated_at.isoformat() if tenant.updated_at else None
            },
            'message': 'ok'
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'获取租户使用统计失败: {str(e)}'
        }), 500


@bp.route('/tenants/stats', methods=['GET'])
@token_required
@super_admin_required
def get_tenants_stats():
    """获取所有租户的统计信息 (v2版本)"""
    try:
        from sqlalchemy import func
        from app.models.tenant import UserTenant
        from app import db
        
        # 租户总数统计
        total_tenants = Tenant.query.count()
        active_tenants = Tenant.query.filter_by(status='active').count()
        inactive_tenants = Tenant.query.filter_by(status='inactive').count()
        suspended_tenants = Tenant.query.filter_by(status='suspended').count()
        
        # 订阅级别统计
        subscription_stats = db.session.query(
            Tenant.subscription_level,
            func.count(Tenant.id).label('count')
        ).group_by(Tenant.subscription_level).all()
        
        subscription_distribution = {}
        for level, count in subscription_stats:
            subscription_distribution[level] = count
        
        # 用户总数统计
        total_users = UserTenant.query.count()
        
        return jsonify({
            'code': 0,
            'data': {
                'tenant_stats': {
                    'total': total_tenants,
                    'active': active_tenants,
                    'inactive': inactive_tenants,
                    'suspended': suspended_tenants
                },
                'subscription_distribution': subscription_distribution,
                'total_users': total_users
            },
            'message': 'ok'
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'获取统计信息失败: {str(e)}'
        }), 500


@bp.route('/tenants', methods=['GET'])
@token_required
@super_admin_required
def get_tenants():
    """获取租户列表 (v2版本)"""
    try:
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        include_usage = request.args.get('include_usage', 'false').lower() == 'true'
        
        # 构建查询
        query = Tenant.query
        
        # 应用分页
        pagination = query.paginate(
            page=page,
            per_page=size,
            error_out=False
        )
        
        tenants = pagination.items
        
        # 转换为字典列表
        tenants_data = []
        for tenant in tenants:
            tenant_dict = tenant.to_dict(include_usage=include_usage)
            tenants_data.append(tenant_dict)
        
        return jsonify({
            'code': 0,
            'data': {
                'list': tenants_data,
                'total': pagination.total,
                'page': page,
                'size': size
            },
            'message': 'ok'
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'获取租户列表失败: {str(e)}'
        }), 500