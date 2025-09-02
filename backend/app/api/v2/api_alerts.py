from flask import request, jsonify, g
import json
from app.api.v2 import v2_bp
from app.models.alert import Alert
from app.models.task import Task
from app.models.audit_log import AuditLog, AuditAction, ResourceType
from app.utils.auth_decorators import token_required
from app.utils.tenant_context import TenantContext, tenant_required
from sqlalchemy import or_, and_
from datetime import datetime


@v2_bp.route('/api-alerts', methods=['GET'])
@token_required
@tenant_required
def get_api_alerts_v2():
    """
    获取API告警列表 - v2版本（强制租户隔离）
    此版本强制只返回当前用户租户的API告警，不允许查看其他租户数据
    """
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        keyword = request.args.get('keyword', '')
        alert_level = request.args.get('alert_level', '')
        status = request.args.get('status', '')
        api_endpoint = request.args.get('api_endpoint', '')
        task_id = request.args.get('task_id', type=int)
        start_time = request.args.get('start_time', '')
        end_time = request.args.get('end_time', '')
        
        # 基础查询 - 强制按租户过滤
        tenant_id = TenantContext.get_current_tenant_id()
        if not tenant_id:
            return jsonify({'code': 403, 'message': '缺少租户上下文'}), 403
            
        # 查询所有类型任务的告警，排除已删除的记录
        query = Alert.query.join(Task).filter(
            Alert.tenant_id == tenant_id,
            Alert.is_deleted == False
        )
        
        # 添加其他过滤条件
        if keyword:
            query = query.filter(
            or_(
                Alert.title.contains(keyword),
                Alert.content.contains(keyword)
            )
        )
        
        if alert_level:
            query = query.filter(Alert.alert_level == alert_level)
        
        if status:
            query = query.filter(Alert.status == status)
        
        # 添加task_id过滤
        if task_id:
            query = query.filter(Alert.task_id == task_id)
        
        # 添加时间范围过滤
        if start_time:
            try:
                start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
                query = query.filter(Alert.created_at >= start_dt)
            except ValueError:
                pass  # 忽略无效的时间格式
        
        if end_time:
            try:
                end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
                query = query.filter(Alert.created_at <= end_dt)
            except ValueError:
                pass  # 忽略无效的时间格式
        
        # API端点过滤已移除，因为Alert模型中没有api_endpoint字段
        
        # 按创建时间倒序排列
        query = query.order_by(Alert.created_at.desc())
        
        # 分页查询
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # 序列化API告警数据
        api_alerts_data = [alert.to_dict() for alert in pagination.items]
        
        return jsonify({
             'code': 0,
             'data': {
                 'list': api_alerts_data,
                 'total': pagination.total,
                 'page': page,
                 'per_page': per_page
             }
         })
        
    except Exception as e:
        return jsonify({'code': 500, 'message': f'获取API告警列表失败: {str(e)}'}), 500


@v2_bp.route('/api-alerts/<int:api_alert_id>', methods=['GET'])
@token_required
@tenant_required
def get_api_alert_v2(api_alert_id):
    """
    获取单个API告警详情 - v2版本（强制租户隔离）
    """
    try:
        tenant_id = TenantContext.get_current_tenant_id()
        if not tenant_id:
            return jsonify({'code': 403, 'message': '缺少租户上下文'}), 403
            
        api_alert = Alert.query.join(Task).filter(
            and_(Alert.id == api_alert_id, Alert.tenant_id == tenant_id, Task.type == 'api')
        ).first()
        
        if not api_alert:
            return jsonify({'code': 404, 'message': 'API告警不存在或无权限访问'}), 404
        
        return jsonify({'code': 0, 'data': api_alert.to_dict()})
        
    except Exception as e:
        return jsonify({'code': 500, 'message': f'获取API告警详情失败: {str(e)}'}), 500


@v2_bp.route('/api-alerts/<int:api_alert_id>/resolve', methods=['POST'])
@token_required
@tenant_required
def resolve_api_alert_v2(api_alert_id):
    """
    解决API告警 - v2版本（强制租户隔离）
    """
    try:
        tenant_id = TenantContext.get_current_tenant_id()
        if not tenant_id:
            return jsonify({'code': 403, 'message': '缺少租户上下文'}), 403
            
        api_alert = Alert.query.join(Task).filter(
            and_(Alert.id == api_alert_id, Alert.tenant_id == tenant_id, Task.type == 'api')
        ).first()
        
        if not api_alert:
            return jsonify({'code': 404, 'message': 'API告警不存在或无权限访问'}), 404
        
        if api_alert.status == 'resolved':
            return jsonify({'code': 400, 'message': 'API告警已经被解决'}), 400
        
        # 记录原始信息用于审计日志
        original_status = api_alert.status
        
        # 更新告警状态
        api_alert.status = 'resolved'
        api_alert.resolved_at = datetime.utcnow()
        
        from app import db
        db.session.commit()
        
        # 记录审计日志
        try:
            current_user = getattr(g, 'current_user', None)
            details = {
                'alert_id': api_alert.id,
                'alert_title': api_alert.title,
                'task_id': api_alert.task_id,
                'original_status': original_status,
                'new_status': 'resolved',
                'operation_type': 'resolve_alert'
            }
            AuditLog.log_action(
                user_id=current_user.id if current_user else None,
                action=AuditAction.UPDATE_SYSTEM_CONFIG,
                resource_type=ResourceType.SYSTEM,
                resource_id=str(api_alert.id),
                details=json.dumps(details, ensure_ascii=False)
            )
        except Exception as audit_error:
            print(f"审计日志记录失败: {audit_error}")
        
        return jsonify({'code': 0, 'data': {'message': 'API告警已解决'}})
        
    except Exception as e:
        from app import db
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'解决API告警失败: {str(e)}'}), 500


@v2_bp.route('/api-alerts/batch', methods=['DELETE'])
@token_required
@tenant_required
def delete_api_alerts_batch_v2():
    """批量硬删除API告警 - v2版本（强制租户隔离）"""
    try:
        from app import db
        
        data = request.get_json()
        
        if 'alert_ids' not in data or not data['alert_ids']:
            return jsonify({
                'code': 400,
                'message': '缺少alert_ids字段或为空'
            }), 400
        
        alert_ids = data['alert_ids']
        
        # 强制按租户过滤，硬删除API告警
        tenant_id = TenantContext.get_current_tenant_id()
        if not tenant_id:
            return jsonify({'code': 403, 'message': '缺少租户上下文'}), 403
            
        # 只删除API类型任务的告警
        alerts = Alert.query.join(Task).filter(
            Alert.tenant_id == tenant_id,
            Task.type == 'api',
            Alert.id.in_(alert_ids),
            Alert.is_deleted == False
        ).all()
        
        deleted_count = len(alerts)
        
        # 记录删除前的信息用于审计日志
        deleted_alerts_info = []
        for alert in alerts:
            deleted_alerts_info.append({
                'id': alert.id,
                'title': alert.title,
                'task_id': alert.task_id,
                'status': alert.status,
                'level': alert.level
            })
        
        # 硬删除：直接从数据库中删除记录
        for alert in alerts:
            db.session.delete(alert)
        
        db.session.commit()
        
        # 记录审计日志
        try:
            current_user = getattr(g, 'current_user', None)
            details = {
                'deleted_alerts': deleted_alerts_info,
                'deleted_count': deleted_count,
                'operation_type': 'batch_delete_alerts'
            }
            AuditLog.log_action(
                user_id=current_user.id if current_user else None,
                action=AuditAction.DELETE_SYSTEM_CONFIG,
                resource_type=ResourceType.SYSTEM,
                resource_id=','.join([str(alert['id']) for alert in deleted_alerts_info]),
                details=json.dumps(details, ensure_ascii=False)
            )
        except Exception as audit_error:
            print(f"审计日志记录失败: {audit_error}")
        
        return jsonify({
            'code': 0,
            'message': f'成功删除 {deleted_count} 条API告警'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'批量删除API告警失败: {str(e)}'
        }), 500