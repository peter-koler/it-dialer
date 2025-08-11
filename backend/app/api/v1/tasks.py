from flask import request, jsonify
from . import bp
from app import db
from app.models.task import Task
from app.models.result import Result
from app.models.node import Node
import json
import re


@bp.route('/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        enabled = request.args.get('enabled', type=lambda x: x.lower() == 'true')
        task_type = request.args.get('type', type=str)
        keyword = request.args.get('keyword', type=str)
        agent_id = request.args.get('agent_id', type=str)
        
        # 构建查询
        query = Task.query
        
        # 应用过滤条件
        if enabled is not None:
            query = query.filter_by(enabled=enabled)
            
        if task_type:
            query = query.filter_by(type=task_type)
            
        if keyword:
            # 搜索任务名称或目标地址
            search = f"%{keyword}%"
            query = query.filter(
                db.or_(
                    Task.name.like(search),
                    Task.target.like(search)
                )
            )
            
        if agent_id:
            # 筛选指定agent_id的任务
            query = query.filter(
                db.or_(
                    Task.agent_ids.like(f'%{agent_id}%'),
                    Task.agent_ids.is_(None)
                )
            )
        
        # 应用分页
        pagination = query.paginate(
            page=page, 
            per_page=size, 
            error_out=False
        )
        
        tasks = pagination.items
        
        # 转换为字典列表
        tasks_data = [task.to_dict() for task in tasks]
        
        return jsonify({
            'code': 0,
            'data': {
                'list': tasks_data,
                'total': pagination.total
            },
            'message': 'ok'
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'获取任务列表失败: {str(e)}'
        }), 500


@bp.route('/tasks', methods=['POST'])
def create_task():
    """Create a new task"""
    try:
        data = request.get_json()
        
        # 验证TCP任务的数据
        if data.get('type') == 'tcp':
            target = data.get('target', '')
            # 验证目标地址格式 (host:port)
            if not re.match(r'^[^:]+:\d+$', target):
                return jsonify({
                    'code': 400,
                    'data': {},
                    'message': 'TCP任务的目标地址格式不正确，应为 host:port'
                }), 400
        
        # 处理agent_ids
        agent_ids = data.get('agent_ids', [])
        agent_ids_json = json.dumps(agent_ids) if agent_ids else None
        
        # 创建新任务
        task = Task(
            name=data.get('name'),
            type=data.get('type'),
            target=data.get('target'),
            interval=data.get('interval', 60),
            enabled=data.get('enabled', True),
            config=data.get('config'),  # 直接存储config字符串
            agent_ids=agent_ids_json
        )
        
        # 保存到数据库
        db.session.add(task)
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': task.to_dict(),
            'message': '任务创建成功'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'创建任务失败: {str(e)}'
        }), 500


@bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """Get a specific task"""
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({
                'code': 404,
                'data': {},
                'message': '任务不存在'
            }), 404
        
        return jsonify({
            'code': 0,
            'data': task.to_dict(),
            'message': 'ok'
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'获取任务失败: {str(e)}'
        }), 500


@bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update a specific task"""
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({
                'code': 404,
                'data': {},
                'message': '任务不存在'
            }), 404
        
        data = request.get_json()
        
        # 验证TCP任务的数据
        if data.get('type') == 'tcp':
            target = data.get('target', '')
            # 验证目标地址格式 (host:port)
            if not re.match(r'^[^:]+:\d+$', target):
                return jsonify({
                    'code': 400,
                    'data': {},
                    'message': 'TCP任务的目标地址格式不正确，应为 host:port'
                }), 400
        
        # 处理agent_ids
        agent_ids = data.get('agent_ids', [])
        agent_ids_json = json.dumps(agent_ids) if agent_ids else None
        
        # 更新任务字段
        task.name = data.get('name', task.name)
        task.type = data.get('type', task.type)
        task.target = data.get('target', task.target)
        task.interval = data.get('interval', task.interval)
        task.enabled = data.get('enabled', task.enabled)
        task.config = data.get('config', task.config)
        task.agent_ids = agent_ids_json
        
        # 提交更改
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': task.to_dict(),
            'message': '任务更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'更新任务失败: {str(e)}'
        }), 500


@bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a specific task"""
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({
                'code': 404,
                'data': {},
                'message': '任务不存在'
            }), 404
        
        # 同时删除相关的执行结果
        Result.query.filter_by(task_id=task_id).delete()
        
        # 删除任务
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': {},
            'message': '任务删除成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'删除任务失败: {str(e)}'
        }), 500