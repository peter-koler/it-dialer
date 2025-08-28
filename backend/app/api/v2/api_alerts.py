from flask import request, jsonify, g
from app.api.v2 import v2_bp
from app.models.alert import Alert
from app.models.task import Task
from app.utils.auth_decorators import token_required
from app.utils.tenant_context import TenantContext, tenant_required
# 使用Flask的jsonify替代响应工具函数
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
        
        # 基础查询 - 强制按租户过滤
        tenant_id = TenantContext.get_current_tenant_id()
        if not tenant_id:
            return jsonify({'code': 403, 'message': '缺少租户上下文'}), 403
            
        # 只查询API类型任务的告警
        query = Alert.query.join(Task).filter(
            Alert.tenant_id == tenant_id,
            Task.type == 'api'
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
        
        # 更新告警状态
        api_alert.status = 'resolved'
        api_alert.resolved_at = datetime.utcnow()
        
        from app import db
        db.session.commit()
        
        return jsonify({'code': 0, 'data': {'message': 'API告警已解决'}})
        
    except Exception as e:
        from app import db
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'解决API告警失败: {str(e)}'}), 500