# -*- coding: utf-8 -*-
"""
报表订阅管理API
提供报表订阅的创建、查询、更新、删除功能
"""

from flask import Blueprint, request, jsonify
from flask_restx import Api, Resource, fields
from datetime import datetime
import logging

from app.models.report import Report, ReportSubscription
from app.utils.auth_decorators import token_required, admin_required, operator_required, viewer_required
from app import db

# 创建蓝图
subscriptions_bp = Blueprint('subscriptions', __name__)
api = Api(subscriptions_bp, doc='/doc/', title='报表订阅API', description='报表订阅管理功能')

logger = logging.getLogger(__name__)

# API模型定义
subscription_model = api.model('ReportSubscription', {
    'id': fields.Integer(description='订阅ID'),
    'report_id': fields.Integer(required=True, description='报表ID'),
    'user_id': fields.Integer(description='用户ID'),
    'email': fields.String(required=True, description='接收邮箱'),
    'frequency': fields.String(required=True, description='推送频率', enum=['daily', 'weekly', 'monthly']),
    'is_active': fields.Boolean(description='是否激活'),
    'config': fields.Raw(description='订阅配置'),
    'created_at': fields.DateTime(description='创建时间'),
    'updated_at': fields.DateTime(description='更新时间'),
    'report_name': fields.String(description='报表名称')
})

subscription_create_model = api.model('SubscriptionCreate', {
    'report_id': fields.Integer(required=True, description='报表ID'),
    'email': fields.String(required=True, description='接收邮箱'),
    'frequency': fields.String(required=True, description='推送频率', enum=['daily', 'weekly', 'monthly']),
    'is_active': fields.Boolean(description='是否激活', default=True),
    'config': fields.Raw(description='订阅配置')
})

subscription_update_model = api.model('SubscriptionUpdate', {
    'email': fields.String(description='接收邮箱'),
    'frequency': fields.String(description='推送频率', enum=['daily', 'weekly', 'monthly']),
    'is_active': fields.Boolean(description='是否激活'),
    'config': fields.Raw(description='订阅配置')
})


@api.route('/subscriptions')
class SubscriptionListAPI(Resource):
    @api.doc('获取订阅列表')
    @api.marshal_list_with(subscription_model)
    @viewer_required
    def get(self, current_user):
        """获取当前用户的订阅列表"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            report_id = request.args.get('report_id', type=int)
            is_active = request.args.get('is_active')
            
            query = ReportSubscription.query.filter_by(user_id=current_user.id)
            
            if report_id:
                query = query.filter(ReportSubscription.report_id == report_id)
            if is_active is not None:
                query = query.filter(ReportSubscription.is_active == (is_active.lower() == 'true'))
                
            subscriptions = query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            # 添加报表名称信息
            result_items = []
            for subscription in subscriptions.items:
                subscription_dict = {
                    'id': subscription.id,
                    'report_id': subscription.report_id,
                    'user_id': subscription.user_id,
                    'email': subscription.email,
                    'frequency': subscription.frequency,
                    'is_active': subscription.is_active,
                    'config': subscription.config,
                    'created_at': subscription.created_at,
                    'updated_at': subscription.updated_at,
                    'report_name': subscription.report.name if subscription.report else '未知报表'
                }
                result_items.append(subscription_dict)
            
            return {
                'subscriptions': result_items,
                'total': subscriptions.total,
                'pages': subscriptions.pages,
                'current_page': page
            }
        except Exception as e:
            logger.error(f"获取订阅列表失败: {str(e)}")
            api.abort(500, f"获取订阅列表失败: {str(e)}")
    
    @api.doc('创建订阅')
    @api.expect(subscription_create_model)
    @api.marshal_with(subscription_model)
    @operator_required
    def post(self, current_user):
        """创建新的报表订阅"""
        try:
            data = request.get_json()
            
            # 验证必填字段
            if not data.get('report_id'):
                api.abort(400, "报表ID不能为空")
            if not data.get('email'):
                api.abort(400, "接收邮箱不能为空")
            if not data.get('frequency'):
                api.abort(400, "推送频率不能为空")
                
            # 验证报表是否存在
            report = Report.query.get(data['report_id'])
            if not report:
                api.abort(404, "报表不存在")
                
            # 验证推送频率
            valid_frequencies = ['daily', 'weekly', 'monthly']
            if data['frequency'] not in valid_frequencies:
                api.abort(400, f"推送频率必须是: {', '.join(valid_frequencies)}")
                
            # 检查是否已存在相同的订阅
            existing_subscription = ReportSubscription.query.filter_by(
                user_id=current_user.id,
                report_id=data['report_id'],
                email=data['email']
            ).first()
            
            if existing_subscription:
                api.abort(400, "该报表的邮箱订阅已存在")
                
            # 创建订阅
            subscription = ReportSubscription(
                report_id=data['report_id'],
                user_id=current_user.id,
                email=data['email'],
                frequency=data['frequency'],
                is_active=data.get('is_active', True),
                config=data.get('config', {})
            )
            
            db.session.add(subscription)
            db.session.commit()
            
            # 添加报表名称信息
            subscription_dict = {
                'id': subscription.id,
                'report_id': subscription.report_id,
                'user_id': subscription.user_id,
                'email': subscription.email,
                'frequency': subscription.frequency,
                'is_active': subscription.is_active,
                'config': subscription.config,
                'created_at': subscription.created_at,
                'updated_at': subscription.updated_at,
                'report_name': report.name
            }
            
            logger.info(f"用户 {current_user.username} 创建了报表订阅: {report.name} -> {subscription.email}")
            return subscription_dict
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"创建订阅失败: {str(e)}")
            api.abort(500, f"创建订阅失败: {str(e)}")


@api.route('/subscriptions/<int:subscription_id>')
class SubscriptionAPI(Resource):
    @api.doc('获取订阅详情')
    @api.marshal_with(subscription_model)
    @viewer_required
    def get(self, current_user, subscription_id):
        """获取订阅详情"""
        try:
            subscription = ReportSubscription.query.filter_by(
                id=subscription_id,
                user_id=current_user.id
            ).first()
            
            if not subscription:
                api.abort(404, "订阅不存在")
                
            subscription_dict = {
                'id': subscription.id,
                'report_id': subscription.report_id,
                'user_id': subscription.user_id,
                'email': subscription.email,
                'frequency': subscription.frequency,
                'is_active': subscription.is_active,
                'config': subscription.config,
                'created_at': subscription.created_at,
                'updated_at': subscription.updated_at,
                'report_name': subscription.report.name if subscription.report else '未知报表'
            }
            
            return subscription_dict
        except Exception as e:
            logger.error(f"获取订阅详情失败: {str(e)}")
            api.abort(500, f"获取订阅详情失败: {str(e)}")
    
    @api.doc('更新订阅')
    @api.expect(subscription_update_model)
    @api.marshal_with(subscription_model)
    @operator_required
    def put(self, current_user, subscription_id):
        """更新订阅"""
        try:
            subscription = ReportSubscription.query.filter_by(
                id=subscription_id,
                user_id=current_user.id
            ).first()
            
            if not subscription:
                api.abort(404, "订阅不存在")
                
            data = request.get_json()
            
            # 验证推送频率
            if data.get('frequency'):
                valid_frequencies = ['daily', 'weekly', 'monthly']
                if data['frequency'] not in valid_frequencies:
                    api.abort(400, f"推送频率必须是: {', '.join(valid_frequencies)}")
                    
            # 检查邮箱是否与其他订阅冲突
            if data.get('email') and data['email'] != subscription.email:
                existing_subscription = ReportSubscription.query.filter_by(
                    user_id=current_user.id,
                    report_id=subscription.report_id,
                    email=data['email']
                ).first()
                
                if existing_subscription:
                    api.abort(400, "该报表的邮箱订阅已存在")
                    
            # 更新订阅信息
            if data.get('email'):
                subscription.email = data['email']
            if data.get('frequency'):
                subscription.frequency = data['frequency']
            if 'is_active' in data:
                subscription.is_active = data['is_active']
            if 'config' in data:
                subscription.config = data['config']
                
            subscription.updated_at = datetime.utcnow()
            db.session.commit()
            
            subscription_dict = {
                'id': subscription.id,
                'report_id': subscription.report_id,
                'user_id': subscription.user_id,
                'email': subscription.email,
                'frequency': subscription.frequency,
                'is_active': subscription.is_active,
                'config': subscription.config,
                'created_at': subscription.created_at,
                'updated_at': subscription.updated_at,
                'report_name': subscription.report.name if subscription.report else '未知报表'
            }
            
            logger.info(f"用户 {current_user.username} 更新了订阅: {subscription_id}")
            return subscription_dict
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"更新订阅失败: {str(e)}")
            api.abort(500, f"更新订阅失败: {str(e)}")
    
    @api.doc('删除订阅')
    @admin_required
    def delete(self, current_user, subscription_id):
        """删除订阅"""
        try:
            subscription = ReportSubscription.query.filter_by(
                id=subscription_id,
                user_id=current_user.id
            ).first()
            
            if not subscription:
                api.abort(404, "订阅不存在")
                
            db.session.delete(subscription)
            db.session.commit()
            
            logger.info(f"用户 {current_user.username} 删除了订阅: {subscription_id}")
            return {'message': '订阅删除成功'}
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"删除订阅失败: {str(e)}")
            api.abort(500, f"删除订阅失败: {str(e)}")


@api.route('/subscriptions/<int:subscription_id>/toggle')
class SubscriptionToggleAPI(Resource):
    @api.doc('切换订阅状态')
    @operator_required
    def post(self, current_user, subscription_id):
        """切换订阅的激活状态"""
        try:
            subscription = ReportSubscription.query.filter_by(
                id=subscription_id,
                user_id=current_user.id
            ).first()
            
            if not subscription:
                api.abort(404, "订阅不存在")
                
            subscription.is_active = not subscription.is_active
            subscription.updated_at = datetime.utcnow()
            db.session.commit()
            
            status = "激活" if subscription.is_active else "停用"
            logger.info(f"用户 {current_user.username} {status}了订阅: {subscription_id}")
            
            return {
                'message': f'订阅已{status}',
                'is_active': subscription.is_active
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"切换订阅状态失败: {str(e)}")
            api.abort(500, f"切换订阅状态失败: {str(e)}")


@api.route('/subscriptions/frequencies')
class SubscriptionFrequenciesAPI(Resource):
    @api.doc('获取推送频率选项')
    @viewer_required
    def get(self, current_user):
        """获取支持的推送频率选项"""
        return {
            'frequencies': [
                {
                    'value': 'daily',
                    'label': '每日推送',
                    'description': '每天定时推送报表'
                },
                {
                    'value': 'weekly',
                    'label': '每周推送',
                    'description': '每周定时推送报表'
                },
                {
                    'value': 'monthly',
                    'label': '每月推送',
                    'description': '每月定时推送报表'
                }
            ]
        }


@api.route('/reports/<int:report_id>/subscriptions')
class ReportSubscriptionsAPI(Resource):
    @api.doc('获取报表的订阅列表')
    @api.marshal_list_with(subscription_model)
    @viewer_required
    def get(self, current_user, report_id):
        """获取指定报表的订阅列表"""
        try:
            # 验证报表是否存在
            report = Report.query.get_or_404(report_id)
            
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            
            subscriptions = ReportSubscription.query.filter_by(
                report_id=report_id,
                user_id=current_user.id
            ).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            # 添加报表名称信息
            result_items = []
            for subscription in subscriptions.items:
                subscription_dict = {
                    'id': subscription.id,
                    'report_id': subscription.report_id,
                    'user_id': subscription.user_id,
                    'email': subscription.email,
                    'frequency': subscription.frequency,
                    'is_active': subscription.is_active,
                    'config': subscription.config,
                    'created_at': subscription.created_at,
                    'updated_at': subscription.updated_at,
                    'report_name': report.name
                }
                result_items.append(subscription_dict)
            
            return {
                'subscriptions': result_items,
                'total': subscriptions.total,
                'pages': subscriptions.pages,
                'current_page': page,
                'report_name': report.name
            }
        except Exception as e:
            logger.error(f"获取报表订阅列表失败: {str(e)}")
            api.abort(500, f"获取报表订阅列表失败: {str(e)}")