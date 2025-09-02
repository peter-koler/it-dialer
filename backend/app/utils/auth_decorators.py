from functools import wraps
from flask import request, jsonify, g
import jwt
from app.config import Config
from app.models.user import User
from app.models.tenant import UserTenant, Tenant


def token_required(f):
    """JWT认证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 从请求头获取token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({
                    'code': 401,
                    'data': {},
                    'message': 'Token格式错误'
                }), 401
        
        if not token:
            return jsonify({
                'code': 401,
                'data': {},
                'message': '缺少认证token'
            }), 401
        
        try:
            # 解码token
            data = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
            current_user = User.query.filter_by(id=data['user_id']).first()
            
            if not current_user or current_user.status != 1:
                return jsonify({
                    'code': 401,
                    'data': {},
                    'message': '用户不存在或已被禁用'
                }), 401
            
            # 验证租户信息
            tenant_id = data.get('tenant_id')
            tenant_role = data.get('tenant_role', 'user')
            
            # 超级管理员不需要租户ID和UserTenant记录
            if tenant_role == 'super_admin':
                # 超级管理员可以不指定租户ID，或者指定任意租户ID
                if tenant_id:
                    current_tenant = Tenant.query.filter_by(id=tenant_id).first()
                    if not current_tenant or current_tenant.status != 'active':
                        return jsonify({
                            'code': 403,
                            'data': {},
                            'message': '租户不存在或已被禁用'
                        }), 403
                else:
                    current_tenant = None
            else:
                # 普通用户必须有租户ID
                if not tenant_id:
                    return jsonify({
                        'code': 401,
                        'data': {},
                        'message': 'Token中缺少租户信息'
                    }), 401
                
                # 验证用户是否有权限访问该租户
                user_tenant = UserTenant.query.filter_by(
                    user_id=current_user.id,
                    tenant_id=tenant_id
                ).first()
                
                if not user_tenant:
                    return jsonify({
                        'code': 403,
                        'data': {},
                        'message': '用户无权限访问该租户'
                    }), 403
                
                # 从UserTenant表中获取实际的租户角色
                tenant_role = user_tenant.role
                
                # 获取租户信息
                current_tenant = Tenant.query.filter_by(id=tenant_id).first()
                if not current_tenant or current_tenant.status != 'active':
                    return jsonify({
                        'code': 403,
                        'data': {},
                        'message': '租户不存在或已被禁用'
                    }), 403
            
            # 将当前用户和租户信息存储到g对象中
            g.current_user = current_user
            g.current_tenant = current_tenant
            g.tenant_id = tenant_id
            g.tenant_role = tenant_role
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                'code': 401,
                'data': {},
                'message': 'Token已过期'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'code': 401,
                'data': {},
                'message': '无效的token'
            }), 401
        except Exception as e:
            return jsonify({
                'code': 401,
                'data': {},
                'message': f'Token验证失败: {str(e)}'
            }), 401
        
        # 检查函数是否需要current_user参数
        import inspect
        sig = inspect.signature(f)
        if 'current_user' in sig.parameters:
            return f(current_user, *args, **kwargs)
        else:
            return f(*args, **kwargs)
    
    return decorated


def require_role(required_role):
    """角色权限装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # 首先检查是否已通过token认证
            if not hasattr(g, 'current_user') or not g.current_user:
                return jsonify({
                    'code': 401,
                    'data': {},
                    'message': '请先进行身份认证'
                }), 401
            
            user_role = g.current_user.role
            
            # 角色权限层级：admin > operator > viewer
            role_hierarchy = {
                'viewer': 1,
                'operator': 2,
                'admin': 3
            }
            
            user_level = role_hierarchy.get(user_role, 0)
            required_level = role_hierarchy.get(required_role, 0)
            
            if user_level < required_level:
                return jsonify({
                    'code': 403,
                    'data': {},
                    'message': f'权限不足，需要{required_role}权限'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator


def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    @token_required
    @require_role('admin')
    def decorated(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated


def operator_required(f):
    """操作员权限装饰器"""
    @wraps(f)
    @token_required
    @require_role('operator')
    def decorated(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated


def viewer_required(f):
    """查看者权限装饰器"""
    @wraps(f)
    @token_required
    @require_role('viewer')
    def decorated(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated