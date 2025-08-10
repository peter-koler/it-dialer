from flask import request, jsonify, make_response
from . import bp
import jwt
import datetime
from functools import wraps
from ...config import Config
from app import db
from app.models.user import User


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
        if user and user.check_password(password) and user.status == 1:
            # Generate tokens
            access_token = jwt.encode({
                'user_id': user.id,
                'username': user.username,
                'role': user.role,
                'exp': datetime.datetime.utcnow() + Config.JWT_ACCESS_TOKEN_EXPIRES
            }, Config.JWT_SECRET_KEY, algorithm='HS256')
            
            refresh_token = jwt.encode({
                'user_id': user.id,
                'username': user.username,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
            }, Config.JWT_SECRET_KEY, algorithm='HS256')
            
            response = make_response(jsonify({
                'code': 0,
                'data': {
                    'access_token': access_token,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'role': user.role
                    }
                },
                'message': 'Login successful'
            }))
            
            response.set_cookie('refresh_token', refresh_token, httponly=True)
            return response
        
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
                'exp': datetime.datetime.utcnow() + Config.JWT_ACCESS_TOKEN_EXPIRES
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