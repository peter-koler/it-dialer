# -*- coding: utf-8 -*-
"""
审计日志API - v2版本
提供审计日志查询功能，支持多租户隔离
"""

from flask import request, jsonify
from app.api.v2 import v2_bp
from app.utils.auth_decorators import token_required
from app.utils.tenant_context import TenantContext, tenant_required
from app.models.audit_log import AuditLog, AuditAction, ResourceType
from app.models.user import User
from app.models.tenant import Tenant, UserTenant

from app import db
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@v2_bp.route('/audit-logs', methods=['GET'])
@token_required
@tenant_required
def get_audit_logs(current_user):
    """
    获取审计日志列表
    
    超级管理员可以查看所有租户的审计日志
    租户管理员只能查看当前租户的审计日志
    """
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        action = request.args.get('action', type=str)
        resource_type = request.args.get('resource_type', type=str)
        user_id = request.args.get('user_id', type=int)
        start_date = request.args.get('start_date', type=str)
        end_date = request.args.get('end_date', type=str)
        tenant_id_param = request.args.get('tenant_id', type=int)  # 仅超级管理员可用
        
        # 限制分页参数
        page_size = min(page_size, 100)
        
        # 获取当前租户ID
        current_tenant_id = TenantContext.get_current_tenant_id()
        
        # 构建基础查询
        query = AuditLog.query
        
        # 权限控制：超级管理员可以查看所有租户，租户管理员只能查看当前租户
        if UserTenant.is_super_admin(current_user.id):
            # 超级管理员可以指定查看特定租户的日志
            if tenant_id_param:
                query = query.filter(AuditLog.tenant_id == tenant_id_param)
            # 如果没有指定tenant_id，则查看所有租户的日志
        else:
            # 租户管理员只能查看当前租户的日志
            if not current_tenant_id:
                return jsonify({'code': 403, 'message': '缺少租户上下文'}), 403
            query = query.filter(AuditLog.tenant_id == current_tenant_id)
        
        # 应用过滤条件
        if action:
            query = query.filter(AuditLog.action == action)
        
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        
        if user_id:
            query = query.filter(
                (AuditLog.user_id == user_id) | (AuditLog.target_user_id == user_id)
            )
        
        # 时间范围过滤
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(AuditLog.created_at >= start_datetime)
            except ValueError:
                return jsonify({'code': 400, 'message': '开始日期格式错误'}), 400
        
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(AuditLog.created_at <= end_datetime)
            except ValueError:
                return jsonify({'code': 400, 'message': '结束日期格式错误'}), 400
        
        # 按创建时间倒序排列
        query = query.order_by(AuditLog.created_at.desc())
        
        # 分页查询
        pagination = query.paginate(
            page=page,
            per_page=page_size,
            error_out=False
        )
        
        # 构建返回数据
        logs = []
        for log in pagination.items:
            log_data = log.to_dict()
            
            # 添加租户名称
            if log.tenant:
                log_data['tenant_name'] = log.tenant.name
            
            logs.append(log_data)
        
        return jsonify({
            'code': 0,
            'message': '获取审计日志成功',
            'data': {
                'list': logs,
                'total': pagination.total,
                'page': page,
                'page_size': page_size,
                'pages': pagination.pages
            }
        })
        
    except Exception as e:
        logger.error(f"获取审计日志失败: {str(e)}")
        return jsonify({'code': 500, 'message': '获取审计日志失败'}), 500


@v2_bp.route('/audit-logs/actions', methods=['GET'])
@token_required
def get_audit_actions(current_user):
    """
    获取可用的审计操作类型列表
    """
    try:
        actions = [
            {'value': AuditAction.CREATE_USER, 'label': '创建用户'},
            {'value': AuditAction.UPDATE_USER, 'label': '更新用户'},
            {'value': AuditAction.DELETE_USER, 'label': '删除用户'},
            {'value': AuditAction.ACTIVATE_USER, 'label': '激活用户'},
            {'value': AuditAction.DEACTIVATE_USER, 'label': '停用用户'},
            {'value': AuditAction.RESET_PASSWORD, 'label': '重置密码'},
            {'value': AuditAction.CREATE_TENANT, 'label': '创建租户'},
            {'value': AuditAction.UPDATE_TENANT, 'label': '更新租户'},
            {'value': AuditAction.DELETE_TENANT, 'label': '删除租户'},
            {'value': AuditAction.ADD_USER_TO_TENANT, 'label': '添加用户到租户'},
            {'value': AuditAction.REMOVE_USER_FROM_TENANT, 'label': '从租户移除用户'},
            {'value': AuditAction.UPDATE_USER_ROLE, 'label': '更新用户角色'},
            {'value': AuditAction.UPDATE_SYSTEM_CONFIG, 'label': '更新系统配置'},
            {'value': AuditAction.LOGIN_SUCCESS, 'label': '登录成功'},
            {'value': AuditAction.LOGIN_FAILED, 'label': '登录失败'},
            {'value': AuditAction.LOGOUT, 'label': '退出登录'}
        ]
        
        return jsonify({
            'code': 0,
            'message': '获取操作类型成功',
            'data': actions
        })
        
    except Exception as e:
        logger.error(f"获取操作类型失败: {str(e)}")
        return jsonify({'code': 500, 'message': '获取操作类型失败'}), 500


@v2_bp.route('/audit-logs/resource-types', methods=['GET'])
@token_required
def get_resource_types(current_user):
    """
    获取可用的资源类型列表
    """
    try:
        resource_types = [
            {'value': ResourceType.USER, 'label': '用户'},
            {'value': ResourceType.TENANT, 'label': '租户'},
            {'value': ResourceType.USER_TENANT, 'label': '用户租户关联'},
            {'value': ResourceType.SYSTEM_CONFIG, 'label': '系统配置'},
            {'value': ResourceType.TASK, 'label': '任务'},
            {'value': ResourceType.NODE, 'label': '节点'},
            {'value': ResourceType.ALERT, 'label': '告警'}
        ]
        
        return jsonify({
            'code': 0,
            'message': '获取资源类型成功',
            'data': resource_types
        })
        
    except Exception as e:
        logger.error(f"获取资源类型失败: {str(e)}")
        return jsonify({'code': 500, 'message': '获取资源类型失败'}), 500


@v2_bp.route('/audit-logs/tenants', methods=['GET'])
@token_required
def get_audit_tenants(current_user):
    """
    获取可查询的租户列表（仅超级管理员可用）
    """
    try:
        # 只有超级管理员可以获取所有租户列表
        if not UserTenant.is_super_admin(current_user.id):
            return jsonify({'code': 403, 'message': '权限不足'}), 403
        
        tenants = Tenant.query.filter_by(status='active').all()
        tenant_list = [{
            'id': tenant.id,
            'name': tenant.name,
            'description': tenant.description
        } for tenant in tenants]
        
        return jsonify({
            'code': 0,
            'message': '获取租户列表成功',
            'data': tenant_list
        })
        
    except Exception as e:
        logger.error(f"获取租户列表失败: {str(e)}")
        return jsonify({'code': 500, 'message': '获取租户列表失败'}), 500


@v2_bp.route('/audit-logs/users', methods=['GET'])
@token_required
@tenant_required
def get_audit_users(current_user):
    """
    获取可查询的用户列表
    
    超级管理员可以获取所有用户
    租户管理员只能获取当前租户的用户
    """
    try:
        # 获取当前租户ID
        current_tenant_id = TenantContext.get_current_tenant_id()
        
        if UserTenant.is_super_admin(current_user.id):
            # 超级管理员可以获取所有用户
            users = User.query.filter_by(status=1).all()
        else:
            # 租户管理员只能获取当前租户的用户
            if not current_tenant_id:
                return jsonify({'code': 403, 'message': '缺少租户上下文'}), 403
            
            users = db.session.query(User).join(
                User.user_tenants
            ).filter(
                User.status == 1,
                User.user_tenants.any(tenant_id=current_tenant_id)
            ).all()
        
        user_list = [{
            'id': user.id,
            'username': user.username,
            'email': user.email
        } for user in users]
        
        return jsonify({
            'code': 0,
            'message': '获取用户列表成功',
            'data': user_list
        })
        
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        return jsonify({'code': 500, 'message': '获取用户列表失败'}), 500


@v2_bp.route('/audit-logs/<int:log_id>', methods=['GET'])
@token_required
@tenant_required
def get_audit_log_detail(current_user, log_id):
    """
    获取审计日志详情
    """
    try:
        # 获取当前租户ID
        current_tenant_id = TenantContext.get_current_tenant_id()
        
        # 查询审计日志
        query = AuditLog.query.filter_by(id=log_id)
        
        # 权限控制
        if not UserTenant.is_super_admin(current_user.id):
            if not current_tenant_id:
                return jsonify({'code': 403, 'message': '缺少租户上下文'}), 403
            query = query.filter(AuditLog.tenant_id == current_tenant_id)
        
        log = query.first()
        if not log:
            return jsonify({'code': 404, 'message': '审计日志不存在'}), 404
        
        log_data = log.to_dict()
        
        # 添加租户名称
        if log.tenant:
            log_data['tenant_name'] = log.tenant.name
        
        return jsonify({
            'code': 0,
            'message': '获取审计日志详情成功',
            'data': log_data
        })
        
    except Exception as e:
        logger.error(f"获取审计日志详情失败: {str(e)}")
        return jsonify({'code': 500, 'message': '获取审计日志详情失败'}), 500