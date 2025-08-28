from flask import request, jsonify, g
from app.api.v2 import v2_bp
from app.models.task import Task
from app.models.node import Node
from app.utils.auth_decorators import token_required
from app.utils.tenant_context import TenantContext, tenant_required
from app import db
from datetime import datetime
from sqlalchemy import or_, and_
import json
import re
import traceback


@v2_bp.route('/tasks', methods=['GET'])
@token_required
@tenant_required
def get_tasks_v2():
    """
    获取任务列表 - v2版本（强制租户隔离）
    此版本强制只返回当前用户租户的任务，不允许查看其他租户数据
    """
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        keyword = request.args.get('keyword', '')
        task_type = request.args.get('task_type', '')
        enabled = request.args.get('enabled', '')
        agent_id = request.args.get('agent_id', '')
        
        # 基础查询 - 根据用户角色决定是否按租户过滤
        tenant_id = TenantContext.get_current_tenant_id()
        if not tenant_id:
            return jsonify({'code': 403, 'message': '缺少租户上下文'}), 403
        
        # 检查用户角色，super_admin可以查看所有租户的数据
        if TenantContext.is_super_admin():
            query = Task.query  # super_admin查看所有任务
        else:
            query = Task.query.filter(Task.tenant_id == tenant_id)  # 普通用户只看自己租户的任务
        
        # 添加其他过滤条件
        if keyword:
            query = query.filter(
                or_(
                    Task.name.contains(keyword),
                    Task.target.contains(keyword)
                )
            )
        
        if task_type:
            query = query.filter(Task.type == task_type)
        
        if enabled != '':
            query = query.filter(Task.enabled == (enabled == 'true'))
        
        if agent_id:
            # agent_ids是JSON字符串，需要使用like查询
            query = query.filter(Task.agent_ids.contains(agent_id))
        
        # 按创建时间倒序排列
        query = query.order_by(Task.created_at.desc())
        
        # 分页查询
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # 序列化任务数据
        tasks_data = []
        for task in pagination.items:
            # 使用Task模型的to_dict方法获取完整数据
            task_dict = task.to_dict()
            tasks_data.append(task_dict)
        
        return jsonify({
             'code': 0,
             'data': {
                 'list': tasks_data,
                 'total': pagination.total,
                 'page': page,
                 'per_page': per_page
             }
         })
        
    except Exception as e:
        return jsonify({'code': 500, 'message': f'获取任务列表失败: {str(e)}'}), 500


@v2_bp.route('/tasks/<int:task_id>', methods=['GET'])
@token_required
@tenant_required
def get_task_v2(task_id):
    """
    获取单个任务详情 - v2版本（强制租户隔离）
    """
    try:
        tenant_id = TenantContext.get_current_tenant_id()
        if not tenant_id:
            return jsonify({'code': 403, 'message': '缺少租户上下文'}), 403
        
        # 检查用户角色，super_admin可以查看所有租户的任务
        if TenantContext.is_super_admin():
            task = Task.query.filter(Task.id == task_id).first()
        else:
            task = Task.query.filter(
                and_(Task.id == task_id, Task.tenant_id == tenant_id)
            ).first()
        
        if not task:
            return jsonify({'code': 404, 'message': '任务不存在或无权限访问'}), 404
        
        # 使用Task模型的to_dict方法获取完整数据
        task_dict = task.to_dict()
        
        return jsonify({'code': 0, 'data': task_dict})
        
    except Exception as e:
        return jsonify({'code': 500, 'message': f'获取任务详情失败: {str(e)}'}), 500


@v2_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@token_required
@tenant_required
def update_task_v2(task_id):
    """更新任务 - v2版本（强制租户隔离）"""
    try:
        # 获取租户ID
        tenant_id = TenantContext.get_current_tenant_id()
        if not tenant_id:
            return jsonify({'code': 403, 'message': '缺少租户上下文'}), 403
        
        # 根据用户角色决定查询范围
        if TenantContext.is_super_admin():
            task = Task.query.filter(Task.id == task_id).first()
        else:
            task = Task.query.filter(Task.id == task_id, Task.tenant_id == tenant_id).first()
        
        if not task:
            return jsonify({
                'code': 404,
                'message': '任务不存在或无权限访问'
            }), 404
        
        data = request.get_json()
        
        # 更新字段
        if 'name' in data:
            task.name = data['name']
        if 'target' in data:
            task.target = data['target']
        if 'interval' in data:
            task.interval = data['interval']
        if 'enabled' in data:
            task.enabled = data['enabled']
        if 'agent_ids' in data:
            # 验证Agent是否存在
            if not isinstance(data['agent_ids'], list) or len(data['agent_ids']) == 0:
                return jsonify({
                    'code': 400,
                    'message': '必须选择至少一个Agent'
                }), 400
            
            # 验证所有Agent是否存在
            for agent_id in data['agent_ids']:
                node = Node.query.filter_by(agent_id=agent_id).first()
                if not node:
                    return jsonify({
                        'code': 400,
                        'message': f'Node不存在: ID {agent_id}'
                    }), 400
            
            # 保存为JSON数组字符串
            task.agent_ids = json.dumps(data['agent_ids'])
        
        if 'config' in data:
            # 确保config是字典类型
            config = data['config']
            if isinstance(config, str):
                try:
                    config = json.loads(config)
                except json.JSONDecodeError:
                    return jsonify({
                        'code': 400,
                        'message': 'config字段不是有效的JSON字符串'
                    }), 400
            
            # 如果任务类型是api，验证配置
            if task.type == 'api':
                # 验证steps字段
                if 'steps' not in config or not isinstance(config['steps'], list) or len(config['steps']) == 0:
                    return jsonify({
                        'code': 400,
                        'message': 'API任务配置必须包含至少一个步骤'
                    }), 400
                
                # 验证每个步骤
                for i, step in enumerate(config['steps']):
                    # 验证步骤ID
                    if 'step_id' not in step:
                        return jsonify({
                            'code': 400,
                            'message': f'第{i+1}个步骤缺少step_id字段'
                        }), 400
                    
                    # 验证步骤名称
                    if 'name' not in step:
                        return jsonify({
                            'code': 400,
                            'message': f'第{i+1}个步骤缺少name字段'
                        }), 400
                    
                    # 验证请求信息
                    if 'request' not in step or not isinstance(step['request'], dict):
                        return jsonify({
                            'code': 400,
                            'message': f'第{i+1}个步骤缺少request字段或格式不正确'
                        }), 400
                    
                    step_request = step['request']
                    
                    # 验证URL和方法
                    if 'url' not in step_request:
                        return jsonify({
                            'code': 400,
                            'message': f'第{i+1}个步骤缺少url字段'
                        }), 400
                    
                    if 'method' not in step_request:
                        return jsonify({
                            'code': 400,
                            'message': f'第{i+1}个步骤缺少method字段'
                        }), 400
                
                # 验证变量字段
                if 'variables' in config and isinstance(config['variables'], list):
                    for var in config['variables']:
                        if 'name' not in var or 'value' not in var:
                            return jsonify({
                                'code': 400,
                                'message': '变量必须包含name和value字段'
                            }), 400
                        
                        # 验证变量名格式
                        if not re.match(r'^\$[a-zA-Z][a-zA-Z0-9_]*$', var['name']):
                            return jsonify({
                                'code': 400,
                                'message': f'变量名格式不正确: {var["name"]}，必须以$开头，后跟字母、数字或下划线'
                            }), 400
            
            task.config = json.dumps(config) if isinstance(config, dict) else config
        
        # 处理alarm_config字段
        if 'alarm_config' in data:
            alarm_config = data['alarm_config']
            if alarm_config:
                if isinstance(alarm_config, str):
                    # 如果是字符串，验证是否为有效JSON
                    try:
                        json.loads(alarm_config)
                        task.alarm_config = alarm_config
                    except json.JSONDecodeError:
                        return jsonify({
                            'code': 400,
                            'message': '告警配置格式不正确'
                        }), 400
                elif isinstance(alarm_config, dict):
                    task.alarm_config = json.dumps(alarm_config)
            else:
                task.alarm_config = None
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': task.to_dict(),
            'message': '任务更新成功'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error in update_task_v2: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'message': f'更新任务失败: {str(e)}'
        }), 500


@v2_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@token_required
@tenant_required
def delete_task_v2(task_id):
    """软删除任务 - v2版本（强制租户隔离）"""
    try:
        # 获取租户ID
        tenant_id = TenantContext.get_current_tenant_id()
        if not tenant_id:
            return jsonify({'code': 403, 'message': '缺少租户上下文'}), 403
        
        # 根据用户角色决定查询范围
        if TenantContext.is_super_admin():
            task = Task.query.filter(Task.id == task_id).first()
        else:
            task = Task.query.filter(Task.id == task_id, Task.tenant_id == tenant_id).first()
        
        if not task:
            return jsonify({
                'code': 404,
                'message': '任务不存在或无权限访问'
            }), 404
        
        # 软删除：设置状态为deleted
        task.status = 'deleted'
        task.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'message': '任务删除成功'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error in delete_task_v2: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'message': f'删除任务失败: {str(e)}'
        }), 500