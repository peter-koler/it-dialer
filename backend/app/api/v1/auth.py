from flask import request, jsonify, make_response
from . import bp
import jwt
import datetime
from functools import wraps
from ...config import Config
from app import db
from app.models.user import User
from app.models.tenant import UserTenant
from app.models.audit_log import AuditLog, AuditAction, ResourceType
import json


@bp.route('/auth/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        # 查找用户
        user = User.query.filter_by(username=username).first()
        
        # 验证用户和密码
        if user and user.check_password(password) and (user.status == 1 or user.status == 'active'):
            # 获取用户的租户信息
            user_tenant_objects = UserTenant.get_user_tenants(user.id)
            
            # 如果用户没有关联任何租户，返回错误
            if not user_tenant_objects:
                return jsonify({
                    'code': 403,
                    'data': {},
                    'message': 'User is not associated with any tenant'
                }), 403
            
            # 转换为字典格式
            user_tenants = []
            for ut in user_tenant_objects:
                user_tenants.append({
                    'tenant_id': ut.tenant_id,
                    'tenant_name': ut.tenant.name if ut.tenant else 'Unknown',
                    'role': ut.role
                })
            
            # 默认使用第一个租户（后续可以支持用户选择租户）
            default_tenant = user_tenants[0]
            
            # Generate tokens
            access_token = jwt.encode({
                'user_id': user.id,
                'username': user.username,
                'role': user.role,
                'tenant_id': default_tenant['tenant_id'],
                'tenant_role': default_tenant['role'],
                'exp': datetime.datetime.now() + Config.JWT_ACCESS_TOKEN_EXPIRES
            }, Config.JWT_SECRET_KEY, algorithm='HS256')
            
            refresh_token = jwt.encode({
                'user_id': user.id,
                'username': user.username,
                'tenant_id': default_tenant['tenant_id'],
                'tenant_role': default_tenant['role'],
                'exp': datetime.datetime.now() + datetime.timedelta(days=1)
            }, Config.JWT_SECRET_KEY, algorithm='HS256')
            
            response = make_response(jsonify({
                'code': 0,
                'data': {
                    'access_token': access_token,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'role': user.role,
                        'tenant_id': default_tenant['tenant_id'],
                        'tenant_role': default_tenant['role'],
                        'tenants': user_tenants  # 返回用户所有租户信息
                    }
                },
                'message': 'Login successful'
            }))
            
            response.set_cookie('refresh_token', refresh_token, httponly=True)
            
            # 记录登录成功的审计日志
            try:
                details = {
                    'username': user.username,
                    'tenant_id': default_tenant['tenant_id'],
                    'tenant_name': default_tenant['tenant_name'],
                    'tenant_role': default_tenant['role'],
                    'operation_type': 'login_success'
                }
                
                AuditLog.log_action(
                    tenant_id=default_tenant['tenant_id'],
                    action=AuditAction.LOGIN_SUCCESS,
                    resource_type=ResourceType.USER,
                    user_id=user.id,
                    details=json.dumps(details, ensure_ascii=False),
                    ip_address=request.remote_addr
                )
            except Exception as audit_e:
                # 审计日志记录失败不应影响主要业务逻辑
                print(f"审计日志记录失败: {audit_e}")
            
            return response
        
        # 记录登录失败的审计日志
        try:
            details = {
                'username': username,
                'reason': 'invalid_credentials',
                'operation_type': 'login_failed'
            }
            
            AuditLog.log_action(
                tenant_id=1,  # 使用默认租户ID，因为登录失败时没有租户上下文
                action=AuditAction.LOGIN_FAILED,
                resource_type=ResourceType.USER,
                user_id=None,
                details=json.dumps(details, ensure_ascii=False),
                ip_address=request.remote_addr
            )
        except Exception as audit_e:
            # 审计日志记录失败不应影响主要业务逻辑
            print(f"审计日志记录失败: {audit_e}")
        
        return jsonify({
            'code': 401,
            'data': {},
            'message': 'Invalid credentials'
        }), 401
    except Exception as e:
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'Login failed: {str(e)}'
        }), 500


@bp.route('/auth/refresh', methods=['POST'])
def refresh():
    """Refresh access token"""
    try:
        refresh_token = request.cookies.get('refresh_token')
        
        if not refresh_token:
            return jsonify({
                'code': 401,
                'data': {},
                'message': 'Refresh token is missing'
            }), 401
        
        try:
            data = jwt.decode(refresh_token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
            access_token = jwt.encode({
                'user_id': data['user_id'],
                'username': data['username'],
                'role': data.get('role', 'viewer'),
                'tenant_id': data.get('tenant_id'),
                'tenant_role': data.get('tenant_role', 'user'),
                'exp': datetime.datetime.now() + Config.JWT_ACCESS_TOKEN_EXPIRES
            }, Config.JWT_SECRET_KEY, algorithm='HS256')
            
            return jsonify({
                'code': 0,
                'data': {
                    'access_token': access_token
                },
                'message': 'Token refreshed successfully'
            })
        except jwt.ExpiredSignatureError:
            return jsonify({
                'code': 401,
                'data': {},
                'message': 'Refresh token has expired'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'code': 401,
                'data': {},
                'message': 'Invalid refresh token'
            }), 401
    except Exception as e:
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'Token refresh failed: {str(e)}'
        }), 500