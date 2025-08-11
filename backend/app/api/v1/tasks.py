from flask import request, jsonify
import traceback
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
        tasks_data = []
        for task in tasks:
            try:
                tasks_data.append(task.to_dict())
            except Exception as e:
                print(f"Error converting task {task.id} to dict: {str(e)}")
                print(traceback.format_exc())
                # 即使单个任务转换失败，也继续处理其他任务
                continue
        
        return jsonify({
            'code': 0,
            'data': {
                'list': tasks_data,
                'total': pagination.total
            },
            'message': 'ok'
        })
    except Exception as e:
        print(f"Error in get_tasks: {str(e)}")
        print(traceback.format_exc())
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
            config=json.dumps(data.get('config')) if data.get('config') else None,
            agent_ids=agent_ids_json
        )
        
        db.session.add(task)
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': task.to_dict(),
            'message': 'ok'
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error in create_task: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'创建任务失败: {str(e)}'
        }), 500


@bp.route('/tasks/<int:id>', methods=['GET'])
def get_task(id):
    """Get a specific task"""
    try:
        task = Task.query.get_or_404(id)
        return jsonify({
            'code': 0,
            'data': task.to_dict(),
            'message': 'ok'
        })
    except Exception as e:
        print(f"Error in get_task: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'获取任务失败: {str(e)}'
        }), 500


@bp.route('/tasks/<int:id>', methods=['PUT'])
def update_task(id):
    """Update a specific task"""
    try:
        task = Task.query.get_or_404(id)
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
        
        # 更新任务信息
        task.name = data.get('name', task.name)
        task.type = data.get('type', task.type)
        task.target = data.get('target', task.target)
        task.interval = data.get('interval', task.interval)
        task.enabled = data.get('enabled', task.enabled)
        
        if 'config' in data:
            task.config = json.dumps(data['config']) if data['config'] else None
            
        if 'agent_ids' in data:
            agent_ids = data['agent_ids']
            task.agent_ids = json.dumps(agent_ids) if agent_ids else None
        
        task.updated_at = db.func.now()
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': task.to_dict(),
            'message': 'ok'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error in update_task: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'更新任务失败: {str(e)}'
        }), 500


@bp.route('/tasks/<int:id>', methods=['DELETE'])
def delete_task(id):
    """Delete a specific task"""
    try:
        task = Task.query.get_or_404(id)
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': {},
            'message': 'ok'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error in delete_task: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'删除任务失败: {str(e)}'
        }), 500


@bp.route('/tasks/stats', methods=['GET'])
def get_task_stats():
    """获取任务统计信息"""
    try:
        # 总任务数
        total_tasks = Task.query.count()
        
        # 启用任务数
        enabled_tasks = Task.query.filter_by(enabled=True).count()
        
        # 各类型任务数
        task_types = db.session.query(
            Task.type, 
            db.func.count(Task.id)
        ).group_by(Task.type).all()
        
        # 最近任务结果统计
        recent_results = db.session.query(
            Result.status,
            db.func.count(Result.id)
        ).filter(
            Result.created_at >= db.func.datetime('now', '-1 day')
        ).group_by(Result.status).all()
        
        stats = {
            'total_tasks': total_tasks,
            'enabled_tasks': enabled_tasks,
            'task_types': dict(task_types),
            'recent_results': dict(recent_results)
        }
        
        return jsonify({
            'code': 0,
            'data': stats,
            'message': 'ok'
        })
    except Exception as e:
        print(f"Error in get_task_stats: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'获取任务统计失败: {str(e)}'
        }), 500