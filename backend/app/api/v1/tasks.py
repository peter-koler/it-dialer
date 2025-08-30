from flask import request, jsonify
import traceback
from . import bp
from app import db
from app.models.task import Task
from app.models.node import Node
from app.models.system_variable import SystemVariable
from app.models.result import Result
from app.models.node import Node
from app.utils.auth_decorators import token_required
from app.utils.agent_auth import agent_token_required
from app.utils.tenant_context import get_current_tenant_id, filter_by_tenant, add_tenant_id, tenant_required, check_resource_limit
from datetime import datetime
import json
import re
import os
import sqlite3


@bp.route('/tasks', methods=['GET'])
@token_required
def get_tasks():
    """Get all tasks"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        keyword = request.args.get('keyword', type=str)
        task_type = request.args.get('type', type=str)
        enabled = request.args.get('enabled', type=str)
        agent_id = request.args.get('agent_id', type=str)
        
        # 构建查询，添加租户过滤
        query = filter_by_tenant(Task.query)
        
        # 默认过滤掉已删除的任务
        include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
        if not include_deleted:
            query = query.filter(Task.status != 'deleted')
        
        # 应用过滤条件
        if keyword:
            # 搜索任务名称或目标
            search = f"%{keyword}%"
            query = query.filter(
                db.or_(
                    Task.name.like(search),
                    Task.target.like(search)
                )
            )
        
        if task_type:
            query = query.filter(Task.type == task_type)
        
        if enabled is not None:
            enabled_bool = enabled.lower() == 'true'
            query = query.filter(Task.enabled == enabled_bool)
        
        # 如果指定了agent_id，只返回分配给该Agent的任务
        if agent_id:
            query = query.filter(Task.agent_ids.contains(agent_id))
        
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
        print(f"Error in get_tasks: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'获取任务列表失败: {str(e)}'
        }), 500


@bp.route('/tasks/deleted', methods=['GET'])
@token_required
def get_deleted_tasks():
    """获取已删除的任务列表"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        keyword = request.args.get('keyword', type=str)
        
        # 构建查询，添加租户过滤，只查询已删除的任务
        query = filter_by_tenant(Task.query).filter(Task.status == 'deleted')
        
        # 应用搜索条件
        if keyword:
            search = f"%{keyword}%"
            query = query.filter(
                db.or_(
                    Task.name.like(search),
                    Task.target.like(search)
                )
            )
        
        # 按更新时间倒序排列（删除时间）
        query = query.order_by(Task.updated_at.desc())
        
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
        print(f"Error in get_deleted_tasks: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'获取已删除任务列表失败: {str(e)}'
        }), 500


@bp.route('/tasks/<int:task_id>', methods=['GET'])
@token_required
def get_task(task_id):
    """Get a task by ID"""
    try:
        # 添加租户过滤，确保只能访问自己租户的任务
        task = filter_by_tenant(Task.query).filter(Task.id == task_id).first()
        if not task:
            return jsonify({
                'code': 404,
                'data': {},
                'message': '任务不存在或无权限访问'
            }), 404
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


@bp.route('/tasks', methods=['POST'])
@token_required
@check_resource_limit('tasks')
def create_task():
    """Create a new task"""
    try:
        data = request.get_json()
        print(f"Received data: {data}")  # 添加调试日志
        
        # 验证必要字段
        required_fields = ['name', 'type', 'target', 'interval', 'enabled', 'agent_ids']
        for field in required_fields:
            if field not in data:
                print(f"Missing field: {field}")  # 添加调试日志
                return jsonify({
                    'code': 400,
                    'data': {},
                    'message': f'缺少必要字段: {field}'
                }), 400
        
        print("All required fields present")  # 添加调试日志
        
        # 验证任务类型
        valid_types = ['ping', 'tcp', 'http', 'api']  # 添加了ping和http类型
        if data['type'] not in valid_types:
            return jsonify({
                'code': 400,
                'data': {},
                'message': f'无效的任务类型: {data["type"]}，支持的类型: {valid_types}'
            }), 400
        
        print(f"Valid task type: {data['type']}")  # 添加调试日志
        
        # 验证Agent是否存在
        if not isinstance(data['agent_ids'], list):
            return jsonify({
                'code': 400,
                'data': {},
                'message': 'agent_ids必须是数组格式'
            }), 400
        
        # 如果没有选择Agent，则获取所有可用的Agent
        if len(data['agent_ids']) == 0:
            print("No agents selected, using all available agents")  # 添加调试日志
            all_nodes = Node.query.all()
            if len(all_nodes) == 0:
                return jsonify({
                    'code': 400,
                    'data': {},
                    'message': '系统中没有可用的Agent节点'
                }), 400
            # 使用所有可用节点的agent_id
            data['agent_ids'] = [node.agent_id for node in all_nodes]
            print(f"Using all available agents: {data['agent_ids']}")  # 添加调试日志
            
        # 检查所有Agent是否存在
        for agent_id in data['agent_ids']:
            print(f"Looking for node with agent_id: {agent_id}")  # 添加调试日志
            # 使用filter_by而不是get，因为agent_id不是主键
            node = Node.query.filter_by(agent_id=agent_id).first()
            print(f"Found node: {node}")  # 添加调试日志
            if not node:
                print(f"Node not found: {agent_id}")  # 添加调试日志
                return jsonify({
                    'code': 400,
                    'data': {},
                    'message': f'Node不存在: ID {agent_id}'
                }), 400
        
        print("All nodes found")  # 添加调试日志
        
        # 处理config字段
        config = data.get('config', {})  # 为所有任务类型提供默认空配置
        
        # 验证API任务的配置
        if data['type'] == 'api':
            # 确保config是字典格式
            if 'config' not in data:
                print("API task missing config")  # 添加调试日志
                return jsonify({
                    'code': 400,
                    'data': {},
                    'message': 'API任务必须提供config字段'
                }), 400
            
            # 如果config是字符串，则解析为字典
            config = data['config']
            if isinstance(config, str):
                try:
                    config = json.loads(config)
                    print(f"Parsed config from string: {config}")  # 添加调试日志
                except json.JSONDecodeError as e:
                    print(f"Failed to parse config string: {e}")  # 添加调试日志
                    return jsonify({
                        'code': 400,
                        'data': {},
                        'message': 'API任务配置格式不正确'
                    }), 400
            elif not isinstance(config, dict):
                print("API task config is not dict or string")  # 添加调试日志
                return jsonify({
                    'code': 400,
                    'data': {},
                    'message': 'API任务必须提供config字段'
                }), 400
            
            print(f"API config: {config}")  # 添加调试日志
            
            # V2格式验证：支持initialVariables和authentications
            if 'initialVariables' in config:
                if not isinstance(config['initialVariables'], list):
                    return jsonify({
                        'code': 400,
                        'data': {},
                        'message': 'initialVariables必须是数组格式'
                    }), 400
                
                # 验证每个初始变量
                for var in config['initialVariables']:
                    if not isinstance(var, dict) or 'name' not in var or 'value' not in var:
                        return jsonify({
                            'code': 400,
                            'data': {},
                            'message': '初始变量必须包含name和value字段'
                        }), 400
                    
                    if not var['name'].startswith('$'):
                        return jsonify({
                            'code': 400,
                            'data': {},
                            'message': f'变量名必须以$开头: {var["name"]}'
                        }), 400
            
            # 验证认证配置
            if 'authentications' in config:
                if not isinstance(config['authentications'], list):
                    return jsonify({
                        'code': 400,
                        'data': {},
                        'message': 'authentications必须是数组格式'
                    }), 400
                
                # 验证每个认证配置
                for auth in config['authentications']:
                    if not isinstance(auth, dict) or 'type' not in auth:
                        return jsonify({
                            'code': 400,
                            'data': {},
                            'message': '认证配置必须包含type字段'
                        }), 400
                    
                    auth_type = auth['type']
                    if auth_type not in ['basic', 'digest', 'oauth1', 'oauth2']:
                        return jsonify({
                            'code': 400,
                            'data': {},
                            'message': f'不支持的认证类型: {auth_type}'
                        }), 400
            
            # 验证steps字段（允许没有步骤）
            if 'steps' not in config or not isinstance(config['steps'], list):
                print("API task missing steps or steps is not list")  # 添加调试日志
                return jsonify({
                    'code': 400,
                    'data': {},
                    'message': 'API任务配置必须包含steps数组'
                }), 400
            
            print("API steps validation passed")  # 添加调试日志
            
            # 验证每个步骤（如果存在步骤）
            for i, step in enumerate(config['steps']):
                print(f"Validating step {i}: {step}")  # 添加调试日志
                # 验证步骤ID
                if 'step_id' not in step:
                    return jsonify({
                        'code': 400,
                        'data': {},
                        'message': f'第{i+1}个步骤缺少step_id字段'
                    }), 400
                
                # 验证步骤名称
                if 'name' not in step:
                    return jsonify({
                        'code': 400,
                        'data': {},
                        'message': f'第{i+1}个步骤缺少name字段'
                    }), 400
                
                # 验证请求信息
                if 'request' not in step or not isinstance(step['request'], dict):
                    return jsonify({
                        'code': 400,
                        'data': {},
                        'message': f'第{i+1}个步骤缺少request字段或格式不正确'
                    }), 400
                
                step_request = step['request']
                
                # 验证URL和方法
                if 'url' not in step_request:
                    return jsonify({
                        'code': 400,
                        'data': {},
                        'message': f'第{i+1}个步骤缺少url字段'
                    }), 400
                
                if 'method' not in step_request:
                    return jsonify({
                        'code': 400,
                        'data': {},
                        'message': f'第{i+1}个步骤缺少method字段'
                    }), 400
                
                # 验证变量名格式
                variable_pattern = r'\$[a-zA-Z][a-zA-Z0-9_]*'
                variables_in_url = re.findall(variable_pattern, step_request['url'])
                
                # 验证请求体中的变量
                if 'body' in step_request and isinstance(step_request['body'], dict):
                    body_str = json.dumps(step_request['body'])
                    variables_in_body = re.findall(variable_pattern, body_str)
                    variables_in_url.extend(variables_in_body)
                
                # 验证请求头中的变量
                if 'headers' in step_request and isinstance(step_request['headers'], dict):
                    headers_str = json.dumps(step_request['headers'])
                    variables_in_headers = re.findall(variable_pattern, headers_str)
                    variables_in_url.extend(variables_in_headers)
            
            # 验证变量字段
            if 'variables' in config and isinstance(config['variables'], list):
                for var in config['variables']:
                    if 'name' not in var or 'value' not in var:
                        return jsonify({
                            'code': 400,
                            'data': {},
                            'message': '变量必须包含name和value字段'
                        }), 400
                    
                    # 验证变量名格式
                    if not re.match(r'^\$[a-zA-Z][a-zA-Z0-9_]*$', var['name']):
                        return jsonify({
                            'code': 400,
                            'data': {},
                            'message': f'变量名格式不正确: {var["name"]}，必须以$开头，后跟字母、数字或下划线'
                        }), 400
        
        print("API config validation passed")  # 添加调试日志
        
        # 处理alarm_config字段
        alarm_config = data.get('alarm_config')
        alarm_config_str = None
        if alarm_config:
            if isinstance(alarm_config, str):
                # 如果是字符串，验证是否为有效JSON
                try:
                    json.loads(alarm_config)
                    alarm_config_str = alarm_config
                except json.JSONDecodeError:
                    return jsonify({
                        'code': 400,
                        'data': {},
                        'message': '告警配置格式不正确'
                    }), 400
            elif isinstance(alarm_config, dict):
                alarm_config_str = json.dumps(alarm_config)
        
        # 创建任务
        task = Task(
            name=data['name'],
            type=data['type'],
            target=data['target'],
            interval=data['interval'],
            enabled=data['enabled'],
            agent_ids=json.dumps(data['agent_ids']),  # 保存为JSON数组字符串
            config=json.dumps(config) if isinstance(config, dict) else config,  # 保存为JSON字符串
            alarm_config=alarm_config_str  # 保存告警配置
        )
        
        # 自动添加租户ID
        add_tenant_id(task)
        
        print(f"Creating task: {task}")  # 添加调试日志
        
        db.session.add(task)
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': task.to_dict(),
            'message': '任务创建成功'
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


@bp.route('/tasks/<int:task_id>', methods=['PUT'])
@token_required
def update_task(task_id):
    """Update a task"""
    try:
        # 添加租户过滤，确保只能更新自己租户的任务
        task = filter_by_tenant(Task.query).filter(Task.id == task_id).first()
        if not task:
            return jsonify({
                'code': 404,
                'data': {},
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
                    'data': {},
                    'message': '必须选择至少一个Agent'
                }), 400
            
            # 验证所有Agent是否存在
            for agent_id in data['agent_ids']:
                node = Node.query.filter_by(agent_id=agent_id).first()
                if not node:
                    return jsonify({
                        'code': 400,
                        'data': {},
                        'message': f'Node不存在: ID {agent_id}'
                    }), 400
            
            # 保存为JSON数组字符串
            import json
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
                        'data': {},
                        'message': 'config字段不是有效的JSON字符串'
                    }), 400
            
            # 如果任务类型是api，验证配置
            if task.type == 'api':
                # 验证steps字段
                if 'steps' not in config or not isinstance(config['steps'], list) or len(config['steps']) == 0:
                    return jsonify({
                        'code': 400,
                        'data': {},
                        'message': 'API任务配置必须包含至少一个步骤'
                    }), 400
                
                # 验证每个步骤
                for i, step in enumerate(config['steps']):
                    # 验证步骤ID
                    if 'step_id' not in step:
                        return jsonify({
                            'code': 400,
                            'data': {},
                            'message': f'第{i+1}个步骤缺少step_id字段'
                        }), 400
                    
                    # 验证步骤名称
                    if 'name' not in step:
                        return jsonify({
                            'code': 400,
                            'data': {},
                            'message': f'第{i+1}个步骤缺少name字段'
                        }), 400
                    
                    # 验证请求信息
                    if 'request' not in step or not isinstance(step['request'], dict):
                        return jsonify({
                            'code': 400,
                            'data': {},
                            'message': f'第{i+1}个步骤缺少request字段或格式不正确'
                        }), 400
                    
                    step_request = step['request']
                    
                    # 验证URL和方法
                    if 'url' not in step_request:
                        return jsonify({
                            'code': 400,
                            'data': {},
                            'message': f'第{i+1}个步骤缺少url字段'
                        }), 400
                    
                    if 'method' not in step_request:
                        return jsonify({
                            'code': 400,
                            'data': {},
                            'message': f'第{i+1}个步骤缺少method字段'
                        }), 400
                    
                    # 验证变量名格式
                    variable_pattern = r'\$[a-zA-Z][a-zA-Z0-9_]*'
                    variables_in_url = re.findall(variable_pattern, step_request['url'])
                    
                    # 验证请求体中的变量
                    if 'body' in step_request and isinstance(step_request['body'], dict):
                        body_str = json.dumps(step_request['body'])
                        variables_in_body = re.findall(variable_pattern, body_str)
                        variables_in_url.extend(variables_in_body)
                    
                    # 验证请求头中的变量
                    if 'headers' in step_request and isinstance(step_request['headers'], dict):
                        headers_str = json.dumps(step_request['headers'])
                        variables_in_headers = re.findall(variable_pattern, headers_str)
                        variables_in_url.extend(variables_in_headers)
                
                # 验证变量字段
                if 'variables' in config and isinstance(config['variables'], list):
                    for var in config['variables']:
                        if 'name' not in var or 'value' not in var:
                            return jsonify({
                                'code': 400,
                                'data': {},
                                'message': '变量必须包含name和value字段'
                            }), 400
                        
                        # 验证变量名格式
                        if not re.match(r'^\$[a-zA-Z][a-zA-Z0-9_]*$', var['name']):
                            return jsonify({
                                'code': 400,
                                'data': {},
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
                            'data': {},
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
        print(f"Error in update_task: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'更新任务失败: {str(e)}'
        }), 500


@bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@token_required
def delete_task(task_id):
    """软删除任务"""
    try:
        # 添加租户过滤，确保只能删除自己租户的任务
        task = filter_by_tenant(Task.query).filter(Task.id == task_id).first()
        if not task:
            return jsonify({
                'code': 404,
                'data': {},
                'message': '任务不存在或无权限访问'
            }), 404
        
        # 软删除：设置状态为deleted
        task.status = 'deleted'
        task.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': {},
            'message': '任务删除成功'
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


@bp.route('/tasks/<int:task_id>/restore', methods=['POST'])
@token_required
def restore_task(task_id):
    """恢复已删除的任务"""
    try:
        # 查找已删除的任务
        task = filter_by_tenant(Task.query).filter(
            Task.id == task_id,
            Task.status == 'deleted'
        ).first()
        
        if not task:
            return jsonify({
                'code': 404,
                'data': {},
                'message': '已删除的任务不存在或无权限访问'
            }), 404
        
        # 恢复任务：设置状态为active
        task.status = 'active'
        task.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': task.to_dict(),
            'message': '任务恢复成功'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error in restore_task: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'恢复任务失败: {str(e)}'
        }), 500


@bp.route('/tasks/execute', methods=['POST'])
def execute_task():
    """执行任务"""
    try:
        data = request.get_json()
        
        # 验证必要字段
        if 'task_id' not in data:
            return jsonify({
                'code': 400,
                'message': '缺少必要字段: task_id'
            }), 400
        
        # 获取任务
        task_id = data['task_id']
        task = Task.query.get(task_id)
        if not task:
            return jsonify({
                'code': 404,
                'message': f'任务不存在: ID {task_id}'
            }), 404
        
        # 这里只是模拟任务执行，实际应该发送到Agent执行
        # 对于API任务，我们可以创建一个简单的结果
        if task.type == 'api':
            # 创建结果
            result = Result(
                task_id=task_id,
                status='success',
                data={
                    'steps': [
                        {
                            'step_id': step.get('step_id', f'step{i+1}'),
                            'name': step.get('name', f'步骤{i+1}'),
                            'status': 'success',
                            'duration': 100,  # 模拟耗时100ms
                            'request': step.get('request', {}),
                            'response': {
                                'status_code': 200,
                                'headers': {
                                    'Content-Type': 'application/json'
                                },
                                'body': '{"message": "模拟响应"}'
                            }
                        } for i, step in enumerate(task.config.get('steps', []))
                    ]
                }
            )
            
            db.session.add(result)
            db.session.commit()
            
            return jsonify({
                'code': 0,
                'data': {
                    'result_id': result.id
                },
                'message': '任务执行成功'
            })
        else:
            # 对于其他类型的任务，返回未实现
            return jsonify({
                'code': 501,
                'message': f'暂不支持执行{task.type}类型的任务'
            }), 501
    except Exception as e:
        print(f"Error in execute_task: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'code': 500,
            'message': f'执行任务失败: {str(e)}'
        }), 500


@bp.route('/tasks/agent', methods=['GET'])
@agent_token_required
def get_tasks_for_agent():
    """Agent获取所有任务（不受租户限制）"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        keyword = request.args.get('keyword', type=str)
        task_type = request.args.get('type', type=str)
        enabled = request.args.get('enabled', type=str)
        agent_id = request.args.get('agent_id', type=str)
        
        # 构建查询，Agent可以访问所有任务
        query = Task.query
        
        # 默认过滤掉已删除的任务
        include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
        if not include_deleted:
            query = query.filter(Task.status != 'deleted')
        
        # 应用过滤条件
        if keyword:
            # 搜索任务名称或目标
            search = f"%{keyword}%"
            query = query.filter(
                db.or_(
                    Task.name.like(search),
                    Task.target.like(search)
                )
            )
        
        if task_type:
            query = query.filter(Task.type == task_type)
        
        if enabled is not None:
            enabled_bool = enabled.lower() == 'true'
            query = query.filter(Task.enabled == enabled_bool)
        
        # 如果指定了agent_id，只返回分配给该Agent的任务
        if agent_id:
            query = query.filter(Task.agent_ids.contains(agent_id))
        
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
        print(f"Error in get_tasks_for_agent: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'获取任务列表失败: {str(e)}'
        }), 500


# 创建系统变量表
def create_system_variables_table():
    try:
        # 获取数据库路径
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../instance/app.db')
        
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_variables'")
        if not cursor.fetchone():
            # 创建表
            cursor.execute('''
            CREATE TABLE system_variables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                value TEXT NOT NULL,
                description TEXT,
                is_secret BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            conn.commit()
            print("系统变量表创建成功")
        
        conn.close()
    except Exception as e:
        print(f"创建系统变量表失败: {str(e)}")
        traceback.print_exc()


# 在模块加载时创建表
create_system_variables_table()