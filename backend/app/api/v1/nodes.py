from flask import request, jsonify, make_response
from . import bp
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def check_node_status(app):
    """检查并更新节点状态的定时任务"""
    with app.app_context():
        try:
            from app import db
            from app.models.node import Node
            
            # 获取所有节点
            nodes = Node.query.all()
            
            # 定义超时时间（30分钟）
            timeout_threshold = datetime.now() - timedelta(minutes=30)
            
            for node in nodes:
                # 如果节点最后心跳时间早于超时阈值
                if node.last_heartbeat and node.last_heartbeat < timeout_threshold:
                    # 如果节点当前状态是在线，则更新为超时
                    if node.status == 'online':
                        node.status = 'timeout'
                        node.updated_at = datetime.now()
                        logger.info(f"节点 {node.agent_id} 状态更新为超时")
                # 如果节点从未发送过心跳且创建时间超过30分钟
                elif not node.last_heartbeat and node.created_at < timeout_threshold:
                    if node.status == 'online':
                        node.status = 'timeout'
                        node.updated_at = datetime.now()
                        logger.info(f"节点 {node.agent_id} 状态更新为超时")
            
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"检查节点状态失败: {e}")


@bp.route('/nodes', methods=['GET'])
def get_nodes():
    """获取所有节点列表"""
    try:
        from app import db
        from app.models.node import Node
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        status = request.args.get('status', type=str)
        
        # 构建查询
        query = Node.query
        
        # 应用过滤条件
        if status:
            query = query.filter_by(status=status)
        
        # 按创建时间倒序排列
        query = query.order_by(Node.created_at.desc())
        
        # 应用分页
        pagination = query.paginate(
            page=page, 
            per_page=size, 
            error_out=False
        )
        
        nodes = pagination.items
        
        # 转换为字典列表
        nodes_data = [node.to_dict() for node in nodes]
        
        response = jsonify({
            'code': 0,
            'data': {
                'list': nodes_data,
                'total': pagination.total
            },
            'message': 'ok'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        logger.error(f"获取节点列表失败: {e}")
        response = jsonify({
            'code': 500,
            'data': {},
            'message': f'获取节点列表失败: {str(e)}'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@bp.route('/nodes/<int:node_id>', methods=['GET'])
def get_node(node_id):
    """获取单个节点详情"""
    try:
        from app import db
        from app.models.node import Node
        
        node = Node.query.get(node_id)
        if not node:
            response = jsonify({
                'code': 404,
                'data': {},
                'message': '节点不存在'
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        response = jsonify({
            'code': 0,
            'data': node.to_dict(),
            'message': 'ok'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        logger.error(f"获取节点详情失败: {e}")
        response = jsonify({
            'code': 500,
            'data': {},
            'message': f'获取节点详情失败: {str(e)}'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@bp.route('/nodes/<int:node_id>', methods=['PUT'])
def update_node(node_id):
    """更新节点信息"""
    try:
        from app import db
        from app.models.node import Node
        
        node = Node.query.get(node_id)
        if not node:
            response = jsonify({
                'code': 404,
                'data': {},
                'message': '节点不存在'
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        data = request.get_json()
        
        # 更新节点状态
        if 'status' in data:
            node.status = data['status']
        
        # 更新其他字段
        if 'agent_area' in data:
            node.agent_area = data['agent_area']
        
        node.updated_at = datetime.now()
        
        db.session.commit()
        
        response = jsonify({
            'code': 0,
            'data': node.to_dict(),
            'message': '节点更新成功'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新节点失败: {e}")
        response = jsonify({
            'code': 500,
            'data': {},
            'message': f'更新节点失败: {str(e)}'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@bp.route('/nodes/<int:node_id>', methods=['DELETE'])
def delete_node(node_id):
    """删除节点"""
    try:
        from app import db
        from app.models.node import Node
        
        node = Node.query.get(node_id)
        if not node:
            response = jsonify({
                'code': 404,
                'data': {},
                'message': '节点不存在'
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        db.session.delete(node)
        db.session.commit()
        
        response = jsonify({
            'code': 0,
            'data': {},
            'message': '节点删除成功'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除节点失败: {e}")
        response = jsonify({
            'code': 500,
            'data': {},
            'message': f'删除节点失败: {str(e)}'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@bp.route('/nodes/register', methods=['POST'])
def register_node():
    """注册新节点"""
    try:
        from app import db
        from app.models.node import Node
        
        data = request.get_json()
        
        # 检查必需字段
        required_fields = ['agent_id', 'agent_area', 'ip_address', 'hostname']
        for field in required_fields:
            if field not in data or not data[field]:
                response = jsonify({
                    'code': 400,
                    'data': {},
                    'message': f'缺少必需字段: {field}'
                })
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 400
        
        # 检查节点是否已存在
        node = Node.query.filter_by(agent_id=data['agent_id']).first()
        
        if node:
            # 更新现有节点信息
            node.agent_area = data['agent_area']
            node.ip_address = data['ip_address']
            node.hostname = data['hostname']
            node.last_heartbeat = datetime.now()
            node.status = 'online'  # 新注册的节点状态为在线
            node.updated_at = datetime.now()
        else:
            # 创建新节点
            node = Node(
                agent_id=data['agent_id'],
                agent_area=data['agent_area'],
                ip_address=data['ip_address'],
                hostname=data['hostname'],
                status='online',  # 新节点状态为在线
                last_heartbeat=datetime.now()
            )
            db.session.add(node)
        
        db.session.commit()
        
        response = jsonify({
            'code': 0,
            'data': node.to_dict(),
            'message': '节点注册成功'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"节点注册失败: {e}")
        response = jsonify({
            'code': 500,
            'data': {},
            'message': f'节点注册失败: {str(e)}'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@bp.route('/nodes/heartbeat', methods=['POST'])
def node_heartbeat():
    """处理节点心跳"""
    try:
        from app import db
        from app.models.node import Node
        
        data = request.get_json()
        
        # 检查必需字段
        if 'agent_id' not in data or not data['agent_id']:
            response = jsonify({
                'code': 400,
                'data': {},
                'message': '缺少必需字段: agent_id'
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # 查找节点
        node = Node.query.filter_by(agent_id=data['agent_id']).first()
        if not node:
            response = jsonify({
                'code': 404,
                'data': {},
                'message': '节点不存在'
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        # 更新心跳时间
        node.last_heartbeat = datetime.now()
        
        # 如果节点状态为未上线，则更新为在线
        if node.status == 'offline':
            node.status = 'online'
        
        node.updated_at = datetime.now()
        db.session.commit()
        
        response = jsonify({
            'code': 0,
            'data': {},
            'message': '心跳信息更新成功'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        db.session.rollback()
        logger.error(f"处理心跳信息失败: {e}")
        response = jsonify({
            'code': 500,
            'data': {},
            'message': f'处理心跳信息失败: {str(e)}'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@bp.route('/nodes/status', methods=['PUT'])
def update_node_status():
    """更新节点状态（批量或单个）"""
    try:
        from app import db
        from app.models.node import Node
        
        data = request.get_json()
        
        if 'node_id' in data:
            # 更新单个节点状态
            node = Node.query.get(data['node_id'])
            if not node:
                response = jsonify({
                    'code': 404,
                    'data': {},
                    'message': '节点不存在'
                })
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 404
            
            if 'status' in data:
                node.status = data['status']
                node.updated_at = datetime.now()
                db.session.commit()
                
                response = jsonify({
                    'code': 0,
                    'data': node.to_dict(),
                    'message': '节点状态更新成功'
                })
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response
        elif 'status' in data and 'node_ids' in data:
            # 批量更新节点状态
            nodes = Node.query.filter(Node.id.in_(data['node_ids'])).all()
            for node in nodes:
                node.status = data['status']
                node.updated_at = datetime.now()
            
            db.session.commit()
            
            response = jsonify({
                'code': 0,
                'data': {},
                'message': f'成功更新{len(nodes)}个节点的状态'
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        
        response = jsonify({
            'code': 400,
            'data': {},
            'message': '参数错误'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新节点状态失败: {e}")
        response = jsonify({
            'code': 500,
            'data': {},
            'message': f'更新节点状态失败: {str(e)}'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500