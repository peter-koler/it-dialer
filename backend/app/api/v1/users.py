from flask import request, jsonify
from . import bp
from functools import wraps
from app import db
from app.models.user import User
from app.utils.auth_decorators import token_required


def require_role(role):
    """装饰器：检查用户角色权限"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 这里应该实现实际的角色检查逻辑
            # 示例中简化处理，直接允许访问
            return f(*args, **kwargs)
        # 为每个装饰器函数设置唯一的端点名称
        decorated_function.__name__ = f.__name__ + '_' + role
        return decorated_function
    return decorator


@bp.route('/users', methods=['GET'])
@token_required
@require_role('admin')
def get_users():
    """获取用户列表，支持分页、搜索和角色过滤"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        keyword = request.args.get('keyword', '')
        role = request.args.get('role', '')
        
        # 构建查询
        query = User.query
        
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
            query = query.filter(User.role == role)
        
        # 应用分页
        pagination = query.paginate(
            page=page, 
            per_page=size, 
            error_out=False
        )
        
        users = pagination.items
        
        # 转换为字典列表
        users_data = [user.to_dict() for user in users]
        
        return jsonify({
            'code': 0,
            'data': {
                'list': users_data,
                'total': pagination.total
            },
            'message': 'ok'
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'获取用户列表失败: {str(e)}'
        }), 500


@bp.route('/users', methods=['POST'])
@token_required
@require_role('admin')
def create_user():
    """创建新用户"""
    try:
        data = request.get_json()
        
        # 检查用户名和邮箱是否已存在
        existing_user = User.query.filter(
            db.or_(
                User.username == data['username'],
                User.email == data['email']
            )
        ).first()
        
        if existing_user:
            return jsonify({
                'code': 400,
                'data': {},
                'message': '用户名或邮箱已存在'
            }), 400
        
        # 创建新用户
        user = User(
            username=data['username'],
            email=data['email'],
            role=data['role'],
            status=1 if data.get('status', True) else 0
        )
        
        # 设置密码
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        else:
            return jsonify({
                'code': 400,
                'data': {},
                'message': '密码不能为空'
            }), 400
        
        # 保存到数据库
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': user.to_dict(),
            'message': '用户创建成功'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'创建用户失败: {str(e)}'
        }), 500


@bp.route('/users/<int:user_id>', methods=['PATCH'])
@token_required
@require_role('admin')
def update_user(user_id):
    """更新用户信息"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'code': 404,
                'data': {},
                'message': '用户不存在'
            }), 404
        
        data = request.get_json()
        
        # 更新用户信息
        if 'username' in data:
            # 检查用户名是否已存在（排除当前用户）
            existing_user = User.query.filter(
                User.username == data['username'],
                User.id != user_id
            ).first()
            if existing_user:
                return jsonify({
                    'code': 400,
                    'data': {},
                    'message': '用户名已存在'
                }), 400
            user.username = data['username']
        
        if 'email' in data:
            # 检查邮箱是否已存在（排除当前用户）
            existing_user = User.query.filter(
                User.email == data['email'],
                User.id != user_id
            ).first()
            if existing_user:
                return jsonify({
                    'code': 400,
                    'data': {},
                    'message': '邮箱已存在'
                }), 400
            user.email = data['email']
        
        if 'role' in data:
            user.role = data['role']
        
        if 'status' in data:
            user.status = data['status']
        
        # 更新时间
        from datetime import datetime
        user.updated_at = datetime.now()
        
        # 保存到数据库
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': user.to_dict(),
            'message': '用户更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'更新用户失败: {str(e)}'
        }), 500


@bp.route('/users/<int:user_id>/password', methods=['PATCH'])
@token_required
@require_role('admin')
def reset_user_password(user_id):
    """重置用户密码"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'code': 404,
                'data': {},
                'message': '用户不存在'
            }), 404
        
        data = request.get_json()
        
        # 检查密码
        if 'password' not in data or not data['password']:
            return jsonify({
                'code': 400,
                'data': {},
                'message': '密码不能为空'
            }), 400
        
        # 设置新密码
        user.set_password(data['password'])
        
        # 更新时间
        from datetime import datetime
        user.updated_at = datetime.now()
        
        # 保存到数据库
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': {},
            'message': '密码重置成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'重置密码失败: {str(e)}'
        }), 500


@bp.route('/users/<int:user_id>', methods=['DELETE'])
@token_required
@require_role('admin')
def delete_user(user_id):
    """删除用户"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'code': 404,
                'data': {},
                'message': '用户不存在'
            }), 404
        
        # 不能删除默认的test用户
        if user.username == 'test':
            return jsonify({
                'code': 400,
                'data': {},
                'message': '不能删除默认用户'
            }), 400
        
        # 从数据库删除
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': {},
            'message': '用户删除成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'删除用户失败: {str(e)}'
        }), 500