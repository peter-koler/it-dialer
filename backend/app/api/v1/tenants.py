from flask import request, jsonify, g
from . import bp
from functools import wraps
from app import db
from app.models.tenant import Tenant, UserTenant
from app.models.user import User
from app.models.audit_log import AuditLog, AuditAction, ResourceType
from app.utils.auth_decorators import token_required
from sqlalchemy import func
from datetime import datetime
import uuid
import json


def require_super_admin(f):
    """装饰器：检查超级管理员权限"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 从g对象中获取用户信息（由token_required装饰器设置）
        current_user = getattr(g, 'current_user', None)
        if not current_user:
            return jsonify({'error': '未找到用户信息'}), 401
        
        # 检查是否为超级管理员
        if not UserTenant.is_super_admin(current_user.id):
            return jsonify({'error': '需要超级管理员权限'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/tenants', methods=['GET'])
@token_required
@require_super_admin
def get_tenants():
    """获取租户列表，支持分页、搜索和状态过滤"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        keyword = request.args.get('keyword', '')
        status = request.args.get('status', '')
        subscription_level = request.args.get('subscription_level', '')
        
        # 构建查询
        query = Tenant.query
        
        # 应用搜索条件
        if keyword:
            query = query.filter(
                db.or_(
                    Tenant.name.contains(keyword),
                    Tenant.description.contains(keyword)
                )
            )
        
        # 应用状态过滤
        if status:
            query = query.filter(Tenant.status == status)
        
        # 应用订阅级别过滤
        if subscription_level:
            query = query.filter(Tenant.subscription_level == subscription_level)
        
        # 按创建时间倒序排列
        query = query.order_by(Tenant.created_at.desc())
        
        # 分页
        pagination = query.paginate(
            page=page, per_page=size, error_out=False
        )
        
        # 构建响应数据
        tenants = []
        for tenant in pagination.items:
            tenant_data = tenant.to_dict(include_usage=True)
            # 添加用户数量统计
            user_count = UserTenant.query.filter_by(tenant_id=tenant.id).count()
            tenant_data['user_count'] = user_count
            tenants.append(tenant_data)
        
        return jsonify({
            'tenants': tenants,
            'pagination': {
                'page': page,
                'size': size,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': '获取租户列表失败',
            'message': str(e)
        }), 500


@bp.route('/tenants', methods=['POST'])
@token_required
@require_super_admin
def create_tenant():
    """创建新租户，支持可选创建初始管理员"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        tenant_name = data.get('tenant_name') or data.get('name')
        if not data or not tenant_name:
            return jsonify({'error': '租户名称不能为空'}), 400
        
        # 检查租户名称是否已存在
        existing_tenant = Tenant.query.filter_by(name=tenant_name).first()
        if existing_tenant:
            return jsonify({'error': '租户名称已存在'}), 400
        
        # 获取订阅级别的默认限额
        subscription_level = data.get('subscription_level', 'free')
        default_limits = Tenant.get_default_limits(subscription_level)
        
        # 验证初始管理员信息（如果提供）
        admin_data = data.get('admin')
        if admin_data:
            admin_username = admin_data.get('username')
            admin_password = admin_data.get('password')
            admin_email = admin_data.get('email')
            
            if not admin_username or not admin_password:
                return jsonify({'error': '管理员用户名和密码不能为空'}), 400
            
            # 检查用户名是否已存在
            existing_user = User.query.filter_by(username=admin_username).first()
            if existing_user:
                return jsonify({'error': f'用户名 {admin_username} 已存在'}), 400
        
        # 创建租户
        tenant = Tenant(
            id=str(uuid.uuid4()),
            name=tenant_name,
            description=data.get('description', ''),
            subscription_level=subscription_level,
            max_tasks=data.get('max_tasks', default_limits['max_tasks']),
            max_nodes=data.get('max_nodes', default_limits['max_nodes']),
            max_variables=data.get('max_variables', default_limits['max_variables']),
            max_alerts=data.get('max_alerts', default_limits['max_alerts']),
            max_users=data.get('max_users', default_limits['max_users']),
            status=data.get('status', 'active'),
            meta_data=data.get('meta_data', {})
        )
        
        db.session.add(tenant)
        db.session.flush()  # 获取租户ID
        
        # 创建初始管理员（如果提供）
        admin_user = None
        if admin_data:
            from werkzeug.security import generate_password_hash
            
            admin_user = User(
                username=admin_username,
                password_hash=generate_password_hash(admin_password),
                email=admin_email,
                status='active'
            )
            
            db.session.add(admin_user)
            db.session.flush()  # 获取用户ID
            
            # 创建用户-租户关联
            user_tenant = UserTenant(
                user_id=admin_user.id,
                tenant_id=tenant.id,
                role='tenant_admin'
            )
            
            db.session.add(user_tenant)
        
        db.session.commit()
        
        # 记录审计日志
        current_user = getattr(g, 'current_user', None)
        details = {
            'tenant_name': tenant.name,
            'subscription_level': tenant.subscription_level,
            'max_users': tenant.max_users,
            'created_with_admin': admin_user is not None
        }
        if admin_user:
            details['admin_username'] = admin_user.username
        
        AuditLog.log_action(
            tenant_id=tenant.id,
            action=AuditAction.CREATE_TENANT,
            resource_type=ResourceType.TENANT,
            user_id=current_user.id if current_user else None,
            resource_id=str(tenant.id),
            details=json.dumps(details),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        response_data = {
            'message': '租户创建成功',
            'tenant': tenant.to_dict(include_usage=True)
        }
        
        if admin_user:
            response_data['admin'] = {
                'id': admin_user.id,
                'username': admin_user.username,
                'email': admin_user.email
            }
        
        return jsonify(response_data), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': '创建租户失败',
            'message': str(e)
        }), 500


@bp.route('/tenants/<tenant_id>', methods=['GET'])
@token_required
@require_super_admin
def get_tenant(tenant_id):
    """获取租户详情"""
    try:
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return jsonify({'error': '租户不存在'}), 404
        
        # 获取租户用户列表
        tenant_users = db.session.query(
            User.id, User.username, User.email, UserTenant.role, UserTenant.created_at
        ).join(
            UserTenant, User.id == UserTenant.user_id
        ).filter(
            UserTenant.tenant_id == tenant_id
        ).all()
        
        users = []
        for user_id, username, email, role, created_at in tenant_users:
            users.append({
                'id': user_id,
                'username': username,
                'email': email,
                'role': role,
                'joined_at': created_at.isoformat() if created_at else None
            })
        
        tenant_data = tenant.to_dict(include_usage=True)
        tenant_data['users'] = users
        
        return jsonify({'tenant': tenant_data}), 200
        
    except Exception as e:
        return jsonify({
            'error': '获取租户详情失败',
            'message': str(e)
        }), 500


@bp.route('/tenants/<tenant_id>', methods=['PATCH'])
@token_required
@require_super_admin
def update_tenant(tenant_id):
    """更新租户信息"""
    try:
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return jsonify({'error': '租户不存在'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': '请提供更新数据'}), 400
        
        # 检查租户名称唯一性（如果要更新名称）
        if 'name' in data and data['name'] != tenant.name:
            existing_tenant = Tenant.query.filter_by(name=data['name']).first()
            if existing_tenant:
                return jsonify({'error': '租户名称已存在'}), 400
        
        # 检查max_users限制（如果要更新max_users）
        if 'max_users' in data:
            new_max_users = data['max_users']
            current_user_count = UserTenant.query.filter_by(tenant_id=tenant_id).count()
            
            if new_max_users < current_user_count:
                return jsonify({
                    'error': 'INVALID_MAX_USERS',
                    'message': f'用户数量上限不能小于当前用户数量。当前用户数：{current_user_count}，设置值：{new_max_users}',
                    'current_user_count': current_user_count,
                    'requested_max_users': new_max_users
                }), 400
        
        # 更新字段
        updatable_fields = [
            'name', 'description', 'subscription_level', 'status',
            'max_tasks', 'max_nodes', 'max_variables', 'max_alerts', 'max_users', 'meta_data'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(tenant, field, data[field])
        
        tenant.updated_at = datetime.now()
        db.session.commit()
        
        # 记录审计日志
        current_user = getattr(g, 'current_user', None)
        details = {
            'tenant_name': tenant.name,
            'updated_fields': list(data.keys()),
            'changes': data
        }
        
        AuditLog.log_action(
            tenant_id=tenant.id,
            action=AuditAction.UPDATE_TENANT,
            resource_type=ResourceType.TENANT,
            user_id=current_user.id if current_user else None,
            resource_id=str(tenant.id),
            details=json.dumps(details),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({
            'message': '租户更新成功',
            'tenant': tenant.to_dict(include_usage=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': '更新租户失败',
            'message': str(e)
        }), 500


@bp.route('/tenants/<tenant_id>', methods=['DELETE'])
@token_required
@require_super_admin
def delete_tenant(tenant_id):
    """删除租户（软删除）"""
    try:
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return jsonify({'error': '租户不存在'}), 404
        
        # 检查是否为默认租户
        if tenant.name == 'default':
            return jsonify({'error': '不能删除默认租户'}), 400
        
        # 检查租户是否有活跃用户
        active_users = UserTenant.query.filter_by(tenant_id=tenant_id).count()
        if active_users > 0:
            return jsonify({
                'error': '无法删除租户，请先移除所有用户',
                'active_users': active_users
            }), 400
        
        # 软删除：设置状态为suspended
        tenant.status = 'suspended'
        tenant.updated_at = datetime.now()
        db.session.commit()
        
        # 记录审计日志
        current_user = getattr(g, 'current_user', None)
        details = {
            'tenant_name': tenant.name,
            'action_type': 'soft_delete',
            'reason': 'suspended_by_admin'
        }
        
        AuditLog.log_action(
            tenant_id=tenant.id,
            action=AuditAction.DELETE_TENANT,
            resource_type=ResourceType.TENANT,
            user_id=current_user.id if current_user else None,
            resource_id=str(tenant.id),
            details=json.dumps(details),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({'message': '租户已被暂停'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': '删除租户失败',
            'message': str(e)
        }), 500


def require_tenant_admin_or_super_admin(f):
    """装饰器：检查租户管理员或超级管理员权限"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user = getattr(g, 'current_user', None)
        if not current_user:
            return jsonify({'error': '未找到用户信息'}), 401
        
        # 检查是否为超级管理员
        if UserTenant.is_super_admin(current_user.id):
            return f(*args, **kwargs)
        
        # 检查是否为指定租户的管理员
        tenant_id = kwargs.get('tenant_id')
        if tenant_id and UserTenant.has_permission(current_user.id, tenant_id, 'tenant_admin'):
            return f(*args, **kwargs)
        
        return jsonify({'error': '需要租户管理员或超级管理员权限'}), 403
    return decorated_function


@bp.route('/tenants/<tenant_id>/users', methods=['POST'])
@token_required
@require_tenant_admin_or_super_admin
def create_tenant_user(tenant_id):
    """在租户内创建用户"""
    try:
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return jsonify({'error': '租户不存在'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': '请提供用户数据'}), 400
        
        # 验证必填字段
        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'user')
        status = data.get('status', 'active')
        
        if not username or not password:
            return jsonify({'error': '用户名和密码不能为空'}), 400
        
        # 验证角色
        valid_roles = ['user', 'tenant_admin']
        if role not in valid_roles:
            return jsonify({
                'error': '无效的角色',
                'valid_roles': valid_roles
            }), 400
        
        # 检查当前用户权限（非超级管理员只能在自己的租户内操作）
        current_user = getattr(g, 'current_user', None)
        if not UserTenant.is_super_admin(current_user.id):
            user_tenant_relation = UserTenant.query.filter_by(
                user_id=current_user.id, tenant_id=tenant_id
            ).first()
            if not user_tenant_relation:
                return jsonify({'error': '无权限在此租户内操作'}), 403
        
        # 检查用户数量限制
        current_user_count = UserTenant.query.filter_by(tenant_id=tenant_id).count()
        if current_user_count >= tenant.max_users:
            return jsonify({
                'error': 'USER_LIMIT_REACHED',
                'message': f'租户用户数量已达上限。当前用户数：{current_user_count}，上限：{tenant.max_users}',
                'current_user_count': current_user_count,
                'max_users': tenant.max_users
            }), 400
        
        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({'error': f'用户名 {username} 已存在'}), 400
        
        # 开始事务
        db.session.begin()
        
        # 创建用户
        from werkzeug.security import generate_password_hash
        
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            email=data.get('email', ''),
            status=status
        )
        
        db.session.add(user)
        db.session.flush()  # 获取用户ID
        
        # 创建用户-租户关联
        user_tenant = UserTenant(
            user_id=user.id,
            tenant_id=tenant_id,
            role=role
        )
        
        db.session.add(user_tenant)
        db.session.commit()
        
        # 记录审计日志
        current_user = getattr(g, 'current_user', None)
        details = {
            'tenant_name': tenant.name,
            'created_user': {
                'username': user.username,
                'email': user.email,
                'role': role
            }
        }
        
        AuditLog.log_action(
            tenant_id=tenant.id,
            action=AuditAction.CREATE_USER,
            resource_type=ResourceType.USER,
            user_id=current_user.id if current_user else None,
            target_user_id=user.id,
            resource_id=str(user.id),
            details=json.dumps(details),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({
            'message': '用户创建成功',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'status': user.status,
                'role': role,
                'tenant_id': tenant_id
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': '创建用户失败',
            'message': str(e)
        }), 500


@bp.route('/tenants/<tenant_id>/users', methods=['GET'])
@token_required
@require_tenant_admin_or_super_admin
def get_tenant_users(tenant_id):
    """获取租户内的用户列表"""
    try:
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return jsonify({'error': '租户不存在'}), 404
        
        # 检查当前用户权限（非超级管理员只能查看自己的租户）
        current_user = getattr(g, 'current_user', None)
        if not UserTenant.is_super_admin(current_user.id):
            user_tenant_relation = UserTenant.query.filter_by(
                user_id=current_user.id, tenant_id=tenant_id
            ).first()
            if not user_tenant_relation:
                return jsonify({'error': '无权限查看此租户用户'}), 403
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        keyword = request.args.get('keyword', '')
        role = request.args.get('role', '')
        
        # 构建查询
        query = db.session.query(
            User.id, User.username, User.email, User.status, User.created_at,
            UserTenant.role, UserTenant.created_at.label('joined_at')
        ).join(
            UserTenant, User.id == UserTenant.user_id
        ).filter(
            UserTenant.tenant_id == tenant_id
        )
        
        # 应用搜索条件
        if keyword:
            query = query.filter(
                db.or_(
                    User.username.contains(keyword),
                    User.email.contains(keyword)
                )
            )
        
        # 应用角色过滤
        if role:
            query = query.filter(UserTenant.role == role)
        
        # 分页
        total = query.count()
        users = query.offset((page - 1) * size).limit(size).all()
        
        # 格式化结果
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'status': user.status,
                'role': user.role,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'joined_at': user.joined_at.isoformat() if user.joined_at else None
            })
        
        return jsonify({
            'users': users_data,
            'pagination': {
                'page': page,
                'size': size,
                'total': total,
                'pages': (total + size - 1) // size
            },
            'tenant': {
                'id': tenant.id,
                'name': tenant.name,
                'max_users': tenant.max_users,
                'current_user_count': total
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': '获取用户列表失败',
            'message': str(e)
        }), 500


@bp.route('/tenants/<tenant_id>/users/<int:user_id>', methods=['PUT'])
@token_required
@require_tenant_admin_or_super_admin
def update_tenant_user(tenant_id, user_id):
    """更新租户内的用户信息"""
    try:
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return jsonify({'error': '租户不存在'}), 404
        
        # 检查用户是否在该租户中
        user_tenant = UserTenant.query.filter_by(
            user_id=user_id, tenant_id=tenant_id
        ).first()
        if not user_tenant:
            return jsonify({'error': '用户不在该租户中'}), 404
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        # 检查当前用户权限
        current_user = getattr(g, 'current_user', None)
        if not UserTenant.is_super_admin(current_user.id):
            current_user_tenant = UserTenant.query.filter_by(
                user_id=current_user.id, tenant_id=tenant_id
            ).first()
            if not current_user_tenant:
                return jsonify({'error': '无权限在此租户内操作'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': '请提供更新数据'}), 400
        
        # 更新用户基本信息
        if 'username' in data and data['username'] != user.username:
            # 检查用户名是否已存在
            existing_user = User.query.filter_by(username=data['username']).first()
            if existing_user:
                return jsonify({'error': f'用户名 {data["username"]} 已存在'}), 400
            user.username = data['username']
        
        if 'email' in data:
            user.email = data['email']
        
        if 'status' in data:
            user.status = data['status']
        
        # 更新角色
        if 'role' in data:
            new_role = data['role']
            valid_roles = ['user', 'tenant_admin']
            if new_role not in valid_roles:
                return jsonify({
                    'error': '无效的角色',
                    'valid_roles': valid_roles
                }), 400
            user_tenant.role = new_role
        
        user.updated_at = datetime.now()
        db.session.commit()
        
        # 记录审计日志
        current_user = getattr(g, 'current_user', None)
        details = {
            'tenant_name': tenant.name,
            'updated_user': {
                'username': user.username,
                'email': user.email,
                'role': user_tenant.role
            },
            'updated_fields': list(data.keys()),
            'changes': data
        }
        
        AuditLog.log_action(
            tenant_id=tenant.id,
            action=AuditAction.UPDATE_USER,
            resource_type=ResourceType.USER,
            user_id=current_user.id if current_user else None,
            target_user_id=user.id,
            resource_id=str(user.id),
            details=json.dumps(details),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({
            'message': '用户更新成功',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'status': user.status,
                'role': user_tenant.role,
                'tenant_id': tenant_id
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': '更新用户失败',
            'message': str(e)
        }), 500


@bp.route('/tenants/<tenant_id>/users/<int:user_id>', methods=['DELETE'])
@token_required
@require_tenant_admin_or_super_admin
def delete_tenant_user(tenant_id, user_id):
    """从租户中删除用户"""
    try:
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return jsonify({'error': '租户不存在'}), 404
        
        # 检查用户是否在该租户中
        user_tenant = UserTenant.query.filter_by(
            user_id=user_id, tenant_id=tenant_id
        ).first()
        if not user_tenant:
            return jsonify({'error': '用户不在该租户中'}), 404
        
        # 检查当前用户权限
        current_user = getattr(g, 'current_user', None)
        if not UserTenant.is_super_admin(current_user.id):
            current_user_tenant = UserTenant.query.filter_by(
                user_id=current_user.id, tenant_id=tenant_id
            ).first()
            if not current_user_tenant:
                return jsonify({'error': '无权限在此租户内操作'}), 403
            
            # 不能删除自己
            if current_user.id == user_id:
                return jsonify({'error': '不能删除自己'}), 400
        
        # 检查是否为最后一个管理员
        if user_tenant.role == 'tenant_admin':
            admin_count = UserTenant.query.filter_by(
                tenant_id=tenant_id, role='tenant_admin'
            ).count()
            if admin_count <= 1:
                return jsonify({'error': '不能删除最后一个租户管理员'}), 400
        
        # 获取用户信息用于审计日志
        user = User.query.get(user_id)
        user_info = {
            'username': user.username if user else 'unknown',
            'email': user.email if user else 'unknown',
            'role': user_tenant.role
        }
        
        # 删除用户-租户关联
        db.session.delete(user_tenant)
        
        # 检查用户是否还有其他租户关联
        other_tenant_relations = UserTenant.query.filter_by(user_id=user_id).count()
        if other_tenant_relations == 1:  # 只有当前这一个关联
            # 如果用户没有其他租户关联，可以选择删除用户或保留用户
            # 这里选择保留用户，只删除关联
            pass
        
        db.session.commit()
        
        # 记录审计日志
        current_user = getattr(g, 'current_user', None)
        details = {
            'tenant_name': tenant.name,
            'deleted_user': user_info,
            'action_type': 'remove_from_tenant'
        }
        
        AuditLog.log_action(
            tenant_id=tenant.id,
            action=AuditAction.DELETE_USER,
            resource_type=ResourceType.USER,
            user_id=current_user.id if current_user else None,
            target_user_id=user_id,
            resource_id=str(user_id),
            details=json.dumps(details),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({'message': '用户删除成功'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': '删除用户失败',
            'message': str(e)
        }), 500


@bp.route('/tenants/<tenant_id>/users', methods=['POST'])
@token_required
@require_super_admin
def add_user_to_tenant(tenant_id):
    """将现有用户添加到租户（超级管理员专用）"""
    try:
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return jsonify({'error': '租户不存在'}), 404
        
        data = request.get_json()
        if not data or not data.get('user_id'):
            return jsonify({'error': '用户ID不能为空'}), 400
        
        user_id = data['user_id']
        role = data.get('role', 'user')
        
        # 检查用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        # 检查用户是否已在该租户中
        existing_relation = UserTenant.query.filter_by(
            user_id=user_id, tenant_id=tenant_id
        ).first()
        if existing_relation:
            return jsonify({'error': '用户已在该租户中'}), 400
        
        # 检查用户数量限制
        current_user_count = UserTenant.query.filter_by(tenant_id=tenant_id).count()
        if current_user_count >= tenant.max_users:
            return jsonify({
                'error': 'USER_LIMIT_REACHED',
                'message': f'租户用户数量已达上限。当前用户数：{current_user_count}，上限：{tenant.max_users}'
            }), 400
        
        # 创建用户-租户关联
        user_tenant = UserTenant(
            user_id=user_id,
            tenant_id=tenant_id,
            role=role
        )
        
        db.session.add(user_tenant)
        db.session.commit()
        
        # 记录审计日志
        current_user = getattr(g, 'current_user', None)
        details = {
            'tenant_name': tenant.name,
            'added_user': {
                'username': user.username,
                'email': user.email,
                'role': role
            },
            'action_type': 'add_existing_user_to_tenant'
        }
        
        AuditLog.log_action(
            tenant_id=tenant.id,
            action=AuditAction.ADD_USER_TO_TENANT,
            resource_type=ResourceType.USER,
            user_id=current_user.id if current_user else None,
            target_user_id=user_id,
            resource_id=str(user_id),
            details=json.dumps(details),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({
            'message': '用户添加成功',
            'user_tenant': user_tenant.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': '添加用户失败',
            'message': str(e)
        }), 500


@bp.route('/tenants/<tenant_id>/users/<int:user_id>', methods=['PUT'])
@token_required
@require_super_admin
def update_user_tenant_association(tenant_id, user_id):
    """更新用户租户关联（支持更新用户、租户和角色）"""
    try:
        user_tenant = UserTenant.query.filter_by(
            user_id=user_id, tenant_id=tenant_id
        ).first()
        
        if not user_tenant:
            return jsonify({'error': '用户不在该租户中'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': '请提供更新数据'}), 400
        
        # 获取新的用户ID、租户ID和角色
        new_user_id = data.get('user_id', user_id)
        new_tenant_id = data.get('tenant_id', tenant_id)
        new_role = data.get('role')
        
        # 验证新用户是否存在
        if new_user_id != user_id:
            new_user = User.query.get(new_user_id)
            if not new_user:
                return jsonify({'error': '新用户不存在'}), 404
        
        # 验证新租户是否存在
        if new_tenant_id != tenant_id:
            new_tenant = Tenant.query.get(new_tenant_id)
            if not new_tenant:
                return jsonify({'error': '新租户不存在'}), 404
        
        # 验证角色有效性
        if new_role:
            valid_roles = ['user', 'tenant_admin', 'super_admin']
            if new_role not in valid_roles:
                return jsonify({
                    'error': '无效的角色',
                    'valid_roles': valid_roles
                }), 400
        
        # 如果用户或租户发生变化，检查新的关联是否已存在
        if new_user_id != user_id or new_tenant_id != tenant_id:
            existing_relation = UserTenant.query.filter_by(
                user_id=new_user_id, tenant_id=new_tenant_id
            ).first()
            if existing_relation and existing_relation != user_tenant:
                return jsonify({'error': '新的用户租户关联已存在'}), 400
        
        # 记录原始信息用于审计日志
        original_info = {
            'user_id': user_tenant.user_id,
            'tenant_id': user_tenant.tenant_id,
            'role': user_tenant.role
        }
        
        # 更新关联信息
        user_tenant.user_id = new_user_id
        user_tenant.tenant_id = new_tenant_id
        if new_role:
            user_tenant.role = new_role
        user_tenant.updated_at = datetime.now()
        db.session.commit()
        
        # 记录审计日志
        current_user = getattr(g, 'current_user', None)
        details = {
            'original': original_info,
            'updated': {
                'user_id': new_user_id,
                'tenant_id': new_tenant_id,
                'role': user_tenant.role
            },
            'changes': data,
            'action_type': 'update_user_tenant_association'
        }
        
        AuditLog.log_action(
            tenant_id=new_tenant_id,
            action=AuditAction.UPDATE_USER_ROLE,
            resource_type=ResourceType.USER_TENANT,
            user_id=current_user.id if current_user else None,
            target_user_id=new_user_id,
            resource_id=f"{new_user_id}_{new_tenant_id}",
            details=json.dumps(details),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({
            'message': '用户租户关联更新成功',
            'user_tenant': {
                'user_id': user_tenant.user_id,
                'tenant_id': user_tenant.tenant_id,
                'role': user_tenant.role,
                'updated_at': user_tenant.updated_at.isoformat() if hasattr(user_tenant, 'updated_at') and user_tenant.updated_at else None
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': '更新用户租户关联失败',
            'message': str(e)
        }), 500


@bp.route('/tenants/<tenant_id>/users/<int:user_id>', methods=['DELETE'])
@token_required
@require_super_admin
def remove_user_from_tenant(tenant_id, user_id):
    """从租户中移除用户"""
    try:
        user_tenant = UserTenant.query.filter_by(
            user_id=user_id, tenant_id=tenant_id
        ).first()
        
        if not user_tenant:
            return jsonify({'error': '用户不在该租户中'}), 404
        
        # 获取租户和用户信息用于审计日志
        tenant = Tenant.query.get(tenant_id)
        user = User.query.get(user_id)
        
        user_info = {
            'username': user.username if user else 'unknown',
            'email': user.email if user else 'unknown',
            'role': user_tenant.role
        }
        
        db.session.delete(user_tenant)
        db.session.commit()
        
        # 记录审计日志
        current_user = getattr(g, 'current_user', None)
        details = {
            'tenant_name': tenant.name if tenant else 'unknown',
            'removed_user': user_info,
            'action_type': 'remove_user_from_tenant_by_admin'
        }
        
        AuditLog.log_action(
            tenant_id=tenant_id,
            action=AuditAction.REMOVE_USER_FROM_TENANT,
            resource_type=ResourceType.USER,
            user_id=current_user.id if current_user else None,
            target_user_id=user_id,
            resource_id=str(user_id),
            details=json.dumps(details),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({'message': '用户移除成功'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': '移除用户失败',
            'message': str(e)
        }), 500


@bp.route('/tenants/<tenant_id>/usage', methods=['GET'])
@token_required
@require_super_admin
def get_tenant_usage(tenant_id):
    """获取租户资源使用统计"""
    try:
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return jsonify({'error': '租户不存在'}), 404
        
        usage_stats = tenant.get_usage_stats()
        
        return jsonify({
            'tenant_id': tenant_id,
            'tenant_name': tenant.name,
            'subscription_level': tenant.subscription_level,
            'usage': usage_stats
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': '获取使用统计失败',
            'message': str(e)
        }), 500


@bp.route('/user-tenants', methods=['GET'])
@token_required
@require_super_admin
def get_user_tenants():
    """获取用户租户关联列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        username = request.args.get('username', '')
        tenant_id = request.args.get('tenant_id', '')
        role = request.args.get('role', '')
        
        # 构建查询
        query = db.session.query(
            UserTenant.user_id,
            UserTenant.tenant_id,
            UserTenant.role,
            UserTenant.created_at,
            User.username,
            User.email,
            Tenant.name
        ).join(User, UserTenant.user_id == User.id)\
         .join(Tenant, UserTenant.tenant_id == Tenant.id)
        
        # 应用筛选条件
        if username:
            query = query.filter(User.username.ilike(f'%{username}%'))
        if tenant_id:
            query = query.filter(UserTenant.tenant_id == tenant_id)
        if role:
            query = query.filter(UserTenant.role == role)
        
        # 分页
        total = query.count()
        user_tenants = query.offset((page - 1) * page_size).limit(page_size).all()
        
        # 格式化结果
        result = []
        for ut in user_tenants:
            result.append({
                'id': f"{ut.user_id}_{ut.tenant_id}",  # 组合ID用于前端表格
                'user_id': ut.user_id,
                'tenant_id': ut.tenant_id,
                'role': ut.role,
                'created_at': ut.created_at.isoformat() if ut.created_at else None,
                'username': ut.username,
                'email': ut.email,
                'tenant_name': ut.name
            })
        
        return jsonify({
            'user_tenants': result,
            'total': total,
            'page': page,
            'page_size': page_size
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': '获取用户租户关联列表失败',
            'message': str(e)
        }), 500


@bp.route('/tenants/stats', methods=['GET'])
@token_required
@require_super_admin
def get_tenants_stats():
    """获取所有租户统计信息"""
    try:
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
            'tenant_stats': {
                'total': total_tenants,
                'active': active_tenants,
                'inactive': inactive_tenants,
                'suspended': suspended_tenants
            },
            'subscription_distribution': subscription_distribution,
            'total_users': total_users
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': '获取统计信息失败',
            'message': str(e)
        }), 500