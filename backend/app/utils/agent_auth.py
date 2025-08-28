from functools import wraps
from flask import request, jsonify
from app.config import Config


# Agent固定token，可以配置在环境变量中
AGENT_TOKEN = Config.AGENT_TOKEN if hasattr(Config, 'AGENT_TOKEN') else 'agent-default-token-2024'


def agent_token_required(f):
    """Agent专用认证装饰器
    
    用于Agent相关API的认证，不依赖用户JWT token
    使用固定的Agent token进行认证
    """
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
        
        # 验证Agent token
        if token != AGENT_TOKEN:
            return jsonify({
                'code': 401,
                'data': {},
                'message': '无效的Agent token'
            }), 401
        
        # Agent认证成功，继续执行
        return f(*args, **kwargs)
    
    return decorated


def get_agent_token():
    """获取Agent token
    
    供前端节点管理页面调用，获取Agent配置所需的token
    """
    return AGENT_TOKEN