from flask import request, jsonify
from . import bp
from app import db
from app.models.alert import Alert, AlertConfig
from app.models.task import Task
from app.utils.auth_decorators import token_required
from app.utils.tenant_context import get_current_tenant_id, filter_by_tenant, add_tenant_id, check_resource_limit
from datetime import datetime
import json


@bp.route('/alerts', methods=['GET'])
@token_required
def get_alerts():
    """获取告警列表"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        alert_level = request.args.get('alert_level', '')
        status = request.args.get('status', '')
        task_name = request.args.get('task_name', '')
        start_time = request.args.get('start_time', '')
        end_time = request.args.get('end_time', '')
        
        # 构建查询，添加租户过滤
        query = Alert.query.join(Task).filter(Task.tenant_id == get_current_tenant_id())
        
        # 默认过滤掉已删除的告警
        include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
        if not include_deleted:
            query = query.filter(Alert.is_deleted == False)
        
        # 应用过滤条件
        if alert_level:
            query = query.filter(Alert.alert_level == alert_level)
        
        if status:
            query = query.filter(Alert.status == status)
        
        if task_name:
            query = query.filter(Task.name.like(f'%{task_name}%'))
        
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                query = query.filter(Alert.created_at >= start_dt)
            except ValueError:
                pass
        
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                query = query.filter(Alert.created_at <= end_dt)
            except ValueError:
                pass
        
        # 按创建时间倒序排列
        query = query.order_by(Alert.created_at.desc())
        
        # 分页
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        alerts = [alert.to_dict() for alert in pagination.items]
        
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'alerts': alerts,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages
                }
            }
        })
    
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取告警列表失败: {str(e)}'
        }), 500


@bp.route('/alerts/<int:alert_id>', methods=['GET'])
@token_required
def get_alert_detail(alert_id):
    """获取告警详情"""
    try:
        alert = Alert.query.join(Task).filter(
            Alert.id == alert_id,
            Task.tenant_id == get_current_tenant_id()
        ).first()
        if not alert:
            return jsonify({
                'code': 404,
                'message': '告警不存在或无权限访问'
            }), 404
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': alert.to_dict()
        })
    
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取告警详情失败: {str(e)}'
        }), 500


@bp.route('/alerts', methods=['POST'])
@token_required
@check_resource_limit('alerts')
def create_alert():
    """创建告警"""
    try:
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['task_id', 'alert_type', 'title', 'content']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'code': 400,
                    'message': f'缺少必需字段: {field}'
                }), 400
        
        # 验证任务是否存在
        task = Task.query.get(data['task_id'])
        if not task:
            return jsonify({
                'code': 404,
                'message': '任务不存在'
            }), 404
        
        # 创建告警
        alert = Alert(
            task_id=data['task_id'],
            step_id=data.get('step_id'),
            alert_type=data['alert_type'],
            alert_level=data.get('alert_level', 'warning'),
            title=data['title'],
            content=data['content'],
            trigger_value=data.get('trigger_value'),
            threshold_value=data.get('threshold_value'),
            agent_id=data.get('agent_id'),
            agent_area=data.get('agent_area')
        )
        
        # 设置快照数据
        if 'snapshot_data' in data:
            alert.set_snapshot_data(data['snapshot_data'])
        
        db.session.add(alert)
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'message': '告警创建成功',
            'data': alert.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'创建告警失败: {str(e)}'
        }), 500


@bp.route('/alerts/<int:alert_id>/status', methods=['PUT'])
@token_required
def update_alert_status(alert_id):
    """更新告警状态"""
    try:
        alert = Alert.query.get_or_404(alert_id)
        data = request.get_json()
        
        if 'status' not in data:
            return jsonify({
                'code': 400,
                'message': '缺少status字段'
            }), 400
        
        # 验证状态值
        valid_statuses = ['pending', 'resolved', 'ignored']
        if data['status'] not in valid_statuses:
            return jsonify({
                'code': 400,
                'message': f'无效的状态值，必须是: {", ".join(valid_statuses)}'
            }), 400
        
        alert.status = data['status']
        
        # 如果是解决状态，记录处理信息
        if data['status'] == 'resolved':
            alert.resolved_by = data.get('resolved_by')
            alert.resolved_at = datetime.now()
        
        # 如果是分配，记录分配信息
        if 'assigned_to' in data:
            alert.assigned_to = data['assigned_to']
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'message': '告警状态更新成功',
            'data': alert.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'更新告警状态失败: {str(e)}'
        }), 500


@bp.route('/alerts/batch', methods=['DELETE'])
@token_required
def delete_alerts_batch():
    """批量软删除告警"""
    try:
        data = request.get_json()
        
        if 'alert_ids' not in data or not data['alert_ids']:
            return jsonify({
                'code': 400,
                'message': '缺少alert_ids字段或为空'
            }), 400
        
        alert_ids = data['alert_ids']
        
        # 添加租户过滤，软删除告警
        alerts = filter_by_tenant(Alert.query).filter(
            Alert.id.in_(alert_ids),
            Alert.is_deleted == False
        ).all()
        
        deleted_count = 0
        for alert in alerts:
            alert.is_deleted = True
            alert.deleted_at = datetime.now()
            deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'message': f'成功删除 {deleted_count} 条告警'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'批量删除告警失败: {str(e)}'
        }), 500


@bp.route('/alerts/batch/restore', methods=['POST'])
@token_required
def restore_alerts_batch():
    """批量恢复已删除的告警"""
    try:
        data = request.get_json()
        
        if 'alert_ids' not in data or not data['alert_ids']:
            return jsonify({
                'code': 400,
                'message': '缺少alert_ids字段或为空'
            }), 400
        
        alert_ids = data['alert_ids']
        
        # 添加租户过滤，恢复已删除的告警
        alerts = filter_by_tenant(Alert.query).filter(
            Alert.id.in_(alert_ids),
            Alert.is_deleted == True
        ).all()
        
        restored_count = 0
        for alert in alerts:
            alert.is_deleted = False
            alert.deleted_at = None
            alert.updated_at = datetime.now()
            restored_count += 1
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'message': f'成功恢复 {restored_count} 条告警'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'批量恢复告警失败: {str(e)}'
        }), 500


@bp.route('/alerts/deleted', methods=['GET'])
@token_required
def get_deleted_alerts():
    """获取已删除的告警列表"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        alert_level = request.args.get('alert_level', '')
        task_name = request.args.get('task_name', '')
        
        # 构建查询，添加租户过滤，只查询已删除的告警
        query = Alert.query.join(Task).filter(
            Task.tenant_id == get_current_tenant_id(),
            Alert.is_deleted == True
        )
        
        # 应用过滤条件
        if alert_level:
            query = query.filter(Alert.alert_level == alert_level)
        
        if task_name:
            query = query.filter(Task.name.like(f'%{task_name}%'))
        
        # 按删除时间倒序排列
        query = query.order_by(Alert.deleted_at.desc())
        
        # 分页
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        alerts = pagination.items
        alerts_data = [alert.to_dict() for alert in alerts]
        
        return jsonify({
            'code': 0,
            'data': {
                'alerts': alerts_data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages
                }
            }
        })
    
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取已删除告警列表失败: {str(e)}'
        }), 500


@bp.route('/alerts/batch/status', methods=['PUT'])
@token_required
def update_alerts_status_batch():
    """批量更新告警状态"""
    try:
        data = request.get_json()
        
        if 'alert_ids' not in data or not data['alert_ids']:
            return jsonify({
                'code': 400,
                'message': '缺少alert_ids字段或为空'
            }), 400
        
        if 'status' not in data:
            return jsonify({
                'code': 400,
                'message': '缺少status字段'
            }), 400
        
        alert_ids = data['alert_ids']
        status = data['status']
        
        # 验证状态值
        valid_statuses = ['pending', 'resolved', 'ignored']
        if status not in valid_statuses:
            return jsonify({
                'code': 400,
                'message': f'无效的状态值，必须是: {", ".join(valid_statuses)}'
            }), 400
        
        # 更新告警状态
        alerts = Alert.query.filter(Alert.id.in_(alert_ids)).all()
        updated_count = 0
        
        for alert in alerts:
            alert.status = status
            if status == 'resolved':
                alert.resolved_by = data.get('resolved_by')
                alert.resolved_at = datetime.now()
            updated_count += 1
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'message': f'成功更新 {updated_count} 条告警状态'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'批量更新告警状态失败: {str(e)}'
        }), 500


@bp.route('/alerts/stats', methods=['GET'])
@token_required
def get_alert_stats():
    """获取告警统计信息"""
    try:
        stats = Alert.get_alert_stats()
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': stats
        })
    
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取告警统计失败: {str(e)}'
        }), 500


@bp.route('/alert-configs', methods=['GET'])
@token_required
def get_alert_configs():
    """获取告警配置列表"""
    try:
        task_id = request.args.get('task_id', type=int)
        
        # 构建查询，添加租户过滤
        query = AlertConfig.query.join(Task).filter(Task.tenant_id == get_current_tenant_id())
        
        # 默认过滤掉已删除的配置
        include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
        if not include_deleted:
            query = query.filter(AlertConfig.is_deleted == False)
        
        if task_id:
            query = query.filter(AlertConfig.task_id == task_id)
        
        configs = query.all()
        
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': [config.to_dict() for config in configs]
        })
    
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取告警配置失败: {str(e)}'
        }), 500


@bp.route('/alert-configs', methods=['POST'])
@token_required
def create_alert_config():
    """创建告警配置"""
    try:
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['task_id', 'alert_type', 'config']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'code': 400,
                    'message': f'缺少必需字段: {field}'
                }), 400
        
        # 验证任务是否存在
        task = Task.query.get(data['task_id'])
        if not task:
            return jsonify({
                'code': 404,
                'message': '任务不存在'
            }), 404
        
        # 创建告警配置
        config = AlertConfig(
            task_id=data['task_id'],
            step_id=data.get('step_id'),
            alert_type=data['alert_type'],
            enabled=data.get('enabled', True)
        )
        
        config.set_config(data['config'])
        
        db.session.add(config)
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'message': '告警配置创建成功',
            'data': config.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'创建告警配置失败: {str(e)}'
        }), 500


@bp.route('/alert-configs/<int:config_id>', methods=['PUT'])
@token_required
def update_alert_config(config_id):
    """更新告警配置"""
    try:
        config = AlertConfig.query.get_or_404(config_id)
        data = request.get_json()
        
        # 更新字段
        if 'enabled' in data:
            config.enabled = data['enabled']
        
        if 'config' in data:
            config.set_config(data['config'])
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'message': '告警配置更新成功',
            'data': config.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'更新告警配置失败: {str(e)}'
        }), 500


@bp.route('/alert-configs/<int:config_id>', methods=['DELETE'])
@token_required
def delete_alert_config(config_id):
    """软删除告警配置"""
    try:
        # 添加租户过滤
        config = filter_by_tenant(AlertConfig.query).filter(
            AlertConfig.id == config_id,
            AlertConfig.is_deleted == False
        ).first_or_404()
        
        # 软删除
        config.is_deleted = True
        config.deleted_at = datetime.now()
        config.updated_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'message': '告警配置删除成功'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'删除告警配置失败: {str(e)}'
        }), 500