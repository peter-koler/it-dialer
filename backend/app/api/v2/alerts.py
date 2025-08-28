from flask import request, jsonify, g
from app.api.v2 import v2_bp
from app.models.alert import Alert
from app.utils.auth_decorators import token_required
from app.utils.tenant_context import TenantContext, tenant_required
# 使用Flask的jsonify替代响应工具函数
from sqlalchemy import or_, and_
from datetime import datetime


@v2_bp.route('/alerts', methods=['GET'])
@token_required
@tenant_required
def get_alerts_v2():
    """
    获取拨测告警列表 - v2版本（强制租户隔离）
    此版本强制只返回当前用户租户的告警，不允许查看其他租户数据
    """
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        keyword = request.args.get('keyword', '')
        alert_level = request.args.get('alert_level', '')
        status = request.args.get('status', '')
        task_id = request.args.get('task_id', '')
        
        # 基础查询 - 强制按租户过滤
        tenant_id = TenantContext.get_current_tenant_id()
        if not tenant_id:
            return jsonify({'code': 403, 'message': '缺少租户上下文'}), 403
            
        query = Alert.query.filter(Alert.tenant_id == tenant_id)
        
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
        
        if task_id:
            query = query.filter(Alert.task_id == task_id)
        
        # 按创建时间倒序排列
        query = query.order_by(Alert.created_at.desc())
        
        # 分页查询
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # 序列化告警数据
        alerts_data = []
        for alert in pagination.items:
            alert_dict = {
                'id': alert.id,
                'title': alert.title,
                'content': alert.content,
                'alert_level': alert.alert_level,
                'status': alert.status,
                'task_id': alert.task_id,
                'tenant_id': alert.tenant_id,
                'created_at': alert.created_at.isoformat() if alert.created_at else None,
                'updated_at': alert.updated_at.isoformat() if alert.updated_at else None,
                'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None
            }
            alerts_data.append(alert_dict)
        
        return jsonify({
             'code': 0,
             'data': {
                 'list': alerts_data,
                 'total': pagination.total,
                 'page': page,
                 'per_page': per_page
             }
         })
        
    except Exception as e:
        return jsonify({'code': 500, 'message': f'获取告警列表失败: {str(e)}'}), 500


@v2_bp.route('/alerts/<int:alert_id>', methods=['GET'])
@token_required
@tenant_required
def get_alert_v2(alert_id):
    """
    获取单个告警详情 - v2版本（强制租户隔离）
    """
    try:
        tenant_id = TenantContext.get_current_tenant_id()
        if not tenant_id:
            return jsonify({'code': 403, 'message': '缺少租户上下文'}), 403
            
        alert = Alert.query.filter(
            and_(Alert.id == alert_id, Alert.tenant_id == tenant_id)
        ).first()
        
        if not alert:
            return jsonify({'code': 404, 'message': '告警不存在或无权限访问'}), 404
        
        alert_dict = {
            'id': alert.id,
            'title': alert.title,
            'description': alert.description,
            'alert_level': alert.alert_level,
            'status': alert.status,
            'task_id': alert.task_id,
            'tenant_id': alert.tenant_id,
            'created_at': alert.created_at.isoformat() if alert.created_at else None,
            'updated_at': alert.updated_at.isoformat() if alert.updated_at else None,
            'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None
        }
        
        return jsonify({'code': 0, 'data': alert_dict})
        
    except Exception as e:
        return jsonify({'code': 500, 'message': f'获取告警详情失败: {str(e)}'}), 500


@v2_bp.route('/alerts/<int:alert_id>/resolve', methods=['POST'])
@token_required
@tenant_required
def resolve_alert_v2(alert_id):
    """
    解决告警 - v2版本（强制租户隔离）
    """
    try:
        tenant_id = TenantContext.get_current_tenant_id()
        if not tenant_id:
            return jsonify({'code': 403, 'message': '缺少租户上下文'}), 403
            
        alert = Alert.query.filter(
            and_(Alert.id == alert_id, Alert.tenant_id == tenant_id)
        ).first()
        
        if not alert:
            return jsonify({'code': 404, 'message': '告警不存在或无权限访问'}), 404
        
        if alert.status == 'resolved':
            return jsonify({'code': 400, 'message': '告警已经被解决'}), 400
        
        # 更新告警状态
        alert.status = 'resolved'
        alert.resolved_at = datetime.utcnow()
        
        from app import db
        db.session.commit()
        
        return jsonify({'code': 0, 'data': {'message': '告警已解决'}})
        
    except Exception as e:
        from app import db
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'解决告警失败: {str(e)}'}), 500