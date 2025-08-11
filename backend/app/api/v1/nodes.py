from flask import request, jsonify
from . import bp
from app import db
from app.models.node import Node
from datetime import datetime, timedelta


@bp.route('/nodes', methods=['GET'])
def get_nodes():
    """获取节点列表"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        status = request.args.get('status', type=str)
        keyword = request.args.get('keyword', type=str)
        
        # 构建查询
        query = Node.query
        
        # 应用过滤条件
        if status:
            query = query.filter_by(status=status)
            
        if keyword:
            # 搜索节点名称或agent_id
            search = f"%{keyword}%"
            query = query.filter(
                db.or_(
                    Node.name.like(search),
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
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'获取节点列表失败: {str(e)}'
        }), 500


@bp.route('/nodes/register', methods=['POST'])
def register_node():
    """注册节点"""
    try:
        data = request.get_json()
        
        # 检查节点是否已存在
        node = Node.query.filter_by(agent_id=data.get('agent_id')).first()
        
        if node:
            # 更新现有节点信息
            node.name = data.get('hostname', node.name)
            node.ip_address = data.get('ip_address', node.ip_address)
            node.agent_area = data.get('agent_area', node.agent_area)
            node.status = 'online'
            node.last_heartbeat = datetime.utcnow()
        else:
            # 创建新节点
            node = Node(
                agent_id=data.get('agent_id'),
                name=data.get('hostname', 'Unknown'),
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
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'节点注册失败: {str(e)}'
        }), 500


@bp.route('/nodes/heartbeat', methods=['POST'])
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
        
        # 更新节点状态和心跳时间
        node.status = 'online'
        node.last_heartbeat = datetime.utcnow()
        
        # 提交更改
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': node.to_dict(),
            'message': '心跳更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'心跳更新失败: {str(e)}'
        }), 500


@bp.route('/nodes/status', methods=['PUT'])
def update_node_status():
    """更新节点状态"""
    try:
        data = request.get_json()
        
        # 查找节点
        node = Node.query.get(data.get('id'))
        
        if not node:
            return jsonify({
                'code': 404,
                'data': {},
                'message': '节点不存在'
            }), 404
        
        # 更新节点状态
        node.status = data.get('status', node.status)
        
        # 提交更改
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': node.to_dict(),
            'message': '节点状态更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'节点状态更新失败: {str(e)}'
        }), 500


@bp.route('/nodes/<int:node_id>', methods=['DELETE'])
def delete_node(node_id):
    """删除节点"""
    try:
        node = Node.query.get(node_id)
        
        if not node:
            return jsonify({
                'code': 404,
                'data': {},
                'message': '节点不存在'
            }), 404
        
        db.session.delete(node)
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': {},
            'message': '节点删除成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'节点删除失败: {str(e)}'
        }), 500
