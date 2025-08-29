from flask import request, jsonify
import traceback
from . import bp
from app import db
from app.models.node import Node
from app.utils.auth_decorators import token_required
from app.utils.tenant_context import get_current_tenant_id, check_resource_limit
from app.utils.agent_auth import agent_token_required
from datetime import datetime, timedelta


@bp.route('/nodes', methods=['GET'])
@token_required
def get_nodes():
    """获取节点列表"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        status = request.args.get('status', type=str)
        keyword = request.args.get('keyword', type=str)
        
        # 构建查询（节点现在是全局共享的，不需要租户过滤）
        query = Node.query
        
        # 默认过滤掉已删除的节点
        include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
        if not include_deleted:
            query = query.filter(Node.status != 'deleted')
        
        # 应用过滤条件
        if status:
            query = query.filter_by(status=status)
            
        if keyword:
            # 搜索节点名称或agent_id
            search = f"%{keyword}%"
            query = query.filter(
                db.or_(
                    Node.hostname.like(search),
                    Node.agent_id.like(search)
                )
            )
        
        # 应用分页
        pagination = query.paginate(
            page=page, 
            per_page=size, 
            error_out=False
        )
        
        nodes = pagination.items
        
        # 转换为字典列表
        nodes_data = [node.to_dict() for node in nodes]
        
        return jsonify({
            'code': 0,
            'data': {
                'list': nodes_data,
                'total': pagination.total
            },
            'message': 'ok'
        })
    except Exception as e:
        print(f"Error in get_nodes: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'获取节点列表失败: {str(e)}'
        }), 500


@bp.route('/nodes/deleted', methods=['GET'])
@token_required
def get_deleted_nodes():
    """获取已删除的节点列表"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        keyword = request.args.get('keyword', type=str)
        
        # 构建查询，只查询已删除的节点（节点现在是全局共享的，不需要租户过滤）
        query = Node.query.filter(Node.status == 'deleted')
        
        # 应用搜索条件
        if keyword:
            search = f"%{keyword}%"
            query = query.filter(
                db.or_(
                    Node.hostname.like(search),
                    Node.agent_id.like(search)
                )
            )
        
        # 按更新时间倒序排列（删除时间）
        query = query.order_by(Node.updated_at.desc())
        
        # 应用分页
        pagination = query.paginate(
            page=page, 
            per_page=size, 
            error_out=False
        )
        
        nodes = pagination.items
        
        # 转换为字典列表
        nodes_data = [node.to_dict() for node in nodes]
        
        return jsonify({
            'code': 0,
            'data': {
                'list': nodes_data,
                'total': pagination.total
            },
            'message': 'ok'
        })
    except Exception as e:
        print(f"Error in get_deleted_nodes: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'获取已删除节点列表失败: {str(e)}'
        }), 500


@bp.route('/nodes/register', methods=['POST'])
@agent_token_required
@check_resource_limit('nodes')
def register_node():
    """注册节点"""
    try:
        data = request.get_json()
        
        # 检查节点是否已存在
        node = Node.query.filter_by(agent_id=data.get('agent_id')).first()
        
        if node:
            # 更新现有节点信息
            node.hostname = data.get('hostname', node.hostname)
            node.ip_address = data.get('ip_address', node.ip_address)
            node.agent_area = data.get('agent_area', node.agent_area)
            node.status = 'online'
            node.last_heartbeat = datetime.now()
            node.updated_at = datetime.now()
        else:
            # 创建新节点
            node = Node(
                agent_id=data.get('agent_id'),
                hostname=data.get('hostname', 'Unknown'),
                ip_address=data.get('ip_address', 'Unknown'),
                agent_area=data.get('agent_area', 'default_area'),
                status='online'
            )
            db.session.add(node)
        
        # 提交更改
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': node.to_dict(),
            'message': '节点注册成功'
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error in register_node: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'节点注册失败: {str(e)}'
        }), 500


@bp.route('/nodes/heartbeat', methods=['POST'])
@agent_token_required
def heartbeat():
    """节点心跳"""
    try:
        data = request.get_json()
        
        # 查找节点
        node = Node.query.filter_by(agent_id=data.get('agent_id')).first()
        
        if not node:
            return jsonify({
                'code': 404,
                'data': {},
                'message': '节点不存在'
            }), 404
        
        # 更新心跳时间和状态
        node.status = 'online'
        node.last_heartbeat = datetime.now()
        node.updated_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': node.to_dict(),
            'message': '心跳更新成功'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error in heartbeat: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'心跳更新失败: {str(e)}'
        }), 500


@bp.route('/nodes/agent-token', methods=['GET'])
@token_required
def get_agent_token():
    """获取Agent token
    
    供前端节点管理页面调用，获取Agent配置所需的token
    """
    try:
        from app.utils.agent_auth import get_agent_token
        token = get_agent_token()
        
        return jsonify({
            'code': 0,
            'data': {
                'agent_token': token
            },
            'message': '获取Agent token成功'
        })
    except Exception as e:
        print(f"Error in get_agent_token: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'获取Agent token失败: {str(e)}'
        }), 500


@bp.route('/nodes/<int:id>', methods=['PUT'])
def update_node(id):
    """更新节点"""
    try:
        node = Node.query.get_or_404(id)
        data = request.get_json()
        
        # 更新节点信息
        if 'agent_id' in data:
            node.agent_id = data['agent_id']
        if 'agent_area' in data:
            node.agent_area = data['agent_area']
        if 'ip_address' in data:
            node.ip_address = data['ip_address']
        if 'hostname' in data:
            node.hostname = data['hostname']
        if 'status' in data:
            node.status = data['status']
        
        node.updated_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': node.to_dict(),
            'message': '节点更新成功'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error in update_node: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'节点更新失败: {str(e)}'
        }), 500


@bp.route('/nodes/<int:id>', methods=['DELETE'])
@token_required
def delete_node(id):
    """软删除节点"""
    try:
        # 查找节点（节点现在是全局共享的，不需要租户过滤）
        node = Node.query.filter_by(id=id).first()
        if not node:
            return jsonify({
                'code': 404,
                'data': {},
                'message': '节点不存在'
            }), 404
        
        # 软删除：设置状态为deleted
        node.status = 'deleted'
        node.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': {},
            'message': '节点删除成功'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error in delete_node: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'节点删除失败: {str(e)}'
        }), 500


@bp.route('/nodes/<int:id>/restore', methods=['POST'])
@token_required
def restore_node(id):
    """恢复已删除的节点"""
    try:
        # 查找已删除的节点（节点现在是全局共享的，不需要租户过滤）
        node = Node.query.filter_by(id=id, status='deleted').first()
        if not node:
            return jsonify({
                'code': 404,
                'data': {},
                'message': '已删除的节点不存在'
            }), 404
        
        # 恢复节点：设置状态为offline（需要重新上线）
        node.status = 'offline'
        node.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': node.to_dict(),
            'message': '节点恢复成功'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error in restore_node: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'节点恢复失败: {str(e)}'
        }), 500


@bp.route('/nodes/timeout-check', methods=['POST'])
def check_timeout_nodes():
    """检查超时节点"""
    try:
        # 获取所有在线节点
        online_nodes = Node.query.filter_by(status='online').all()
        
        # 设置超时时间为5分钟
        timeout_threshold = datetime.now() - timedelta(minutes=5)
        
        timeout_count = 0
        for node in online_nodes:
            # 如果最后心跳时间早于超时阈值，则标记为超时
            if node.last_heartbeat and node.last_heartbeat < timeout_threshold:
                node.status = 'timeout'
                node.updated_at = datetime.now()
                timeout_count += 1
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': {
                'timeout_count': timeout_count
            },
            'message': f'检查完成，{timeout_count} 个节点超时'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error in check_timeout_nodes: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'检查超时节点失败: {str(e)}'
        }), 500