# -*- coding: utf-8 -*-
"""
报表管理API
提供报表生成、查询、导出等功能
"""

from flask import Blueprint, request, jsonify, send_file
from flask_restx import Api, Resource, fields
from datetime import datetime, timedelta
import io
import logging

from app.models.report import Report, ReportSubscription
from app.models.task import Task
from app.models.result import Result
from app.utils.auth_decorators import token_required, admin_required, operator_required, viewer_required
from app.utils.export_utils import ExportUtils
from app import db

# 创建蓝图
reports_bp = Blueprint('reports', __name__)
api = Api(reports_bp, doc='/doc/', title='报表管理API', description='报表生成、查询、导出功能')

logger = logging.getLogger(__name__)

# API模型定义
report_model = api.model('Report', {
    'id': fields.Integer(description='报表ID'),
    'name': fields.String(required=True, description='报表名称'),
    'description': fields.String(description='报表描述'),
    'report_type': fields.String(required=True, description='报表类型'),
    'config': fields.Raw(description='报表配置'),
    'created_at': fields.DateTime(description='创建时间'),
    'updated_at': fields.DateTime(description='更新时间')
})

report_create_model = api.model('ReportCreate', {
    'name': fields.String(required=True, description='报表名称'),
    'description': fields.String(description='报表描述'),
    'report_type': fields.String(required=True, description='报表类型'),
    'config': fields.Raw(description='报表配置')
})

export_model = api.model('ExportRequest', {
    'format': fields.String(required=True, description='导出格式', enum=['excel', 'pdf']),
    'start_date': fields.String(description='开始日期 (YYYY-MM-DD)'),
    'end_date': fields.String(description='结束日期 (YYYY-MM-DD)'),
    'filters': fields.Raw(description='过滤条件')
})


@api.route('/reports')
class ReportListAPI(Resource):
    @api.doc('获取报表列表')
    @api.marshal_list_with(report_model)
    @token_required
    @viewer_required
    def get(self, current_user):
        """获取报表列表"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            report_type = request.args.get('type')
            
            query = Report.query
            if report_type:
                query = query.filter(Report.report_type == report_type)
                
            reports = query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'reports': reports.items,
                'total': reports.total,
                'pages': reports.pages,
                'current_page': page
            }
        except Exception as e:
            logger.error(f"获取报表列表失败: {str(e)}")
            api.abort(500, f"获取报表列表失败: {str(e)}")
    
    @api.doc('创建报表')
    @api.expect(report_create_model)
    @api.marshal_with(report_model)
    @token_required
    @operator_required
    def post(self, current_user):
        """创建新报表"""
        try:
            data = request.get_json()
            
            # 验证必填字段
            if not data.get('name'):
                api.abort(400, "报表名称不能为空")
            if not data.get('report_type'):
                api.abort(400, "报表类型不能为空")
                
            # 检查报表名称是否已存在
            existing_report = Report.query.filter_by(name=data['name']).first()
            if existing_report:
                api.abort(400, "报表名称已存在")
                
            # 创建报表
            report = Report(
                name=data['name'],
                description=data.get('description', ''),
                report_type=data['report_type'],
                config=data.get('config', {}),
                created_by=current_user.id
            )
            
            db.session.add(report)
            db.session.commit()
            
            logger.info(f"用户 {current_user.username} 创建了报表: {report.name}")
            return report
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"创建报表失败: {str(e)}")
            api.abort(500, f"创建报表失败: {str(e)}")


@api.route('/reports/<int:report_id>')
class ReportAPI(Resource):
    @api.doc('获取报表详情')
    @api.marshal_with(report_model)
    @token_required
    @viewer_required
    def get(self, current_user, report_id):
        """获取报表详情"""
        try:
            report = Report.query.get_or_404(report_id)
            return report
        except Exception as e:
            logger.error(f"获取报表详情失败: {str(e)}")
            api.abort(500, f"获取报表详情失败: {str(e)}")
    
    @api.doc('更新报表')
    @api.expect(report_create_model)
    @api.marshal_with(report_model)
    @token_required
    @operator_required
    def put(self, current_user, report_id):
        """更新报表"""
        try:
            report = Report.query.get_or_404(report_id)
            data = request.get_json()
            
            # 检查报表名称是否已被其他报表使用
            if data.get('name') and data['name'] != report.name:
                existing_report = Report.query.filter_by(name=data['name']).first()
                if existing_report:
                    api.abort(400, "报表名称已存在")
                    
            # 更新报表信息
            if data.get('name'):
                report.name = data['name']
            if 'description' in data:
                report.description = data['description']
            if data.get('report_type'):
                report.report_type = data['report_type']
            if 'config' in data:
                report.config = data['config']
                
            report.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"用户 {current_user.username} 更新了报表: {report.name}")
            return report
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"更新报表失败: {str(e)}")
            api.abort(500, f"更新报表失败: {str(e)}")
    
    @api.doc('删除报表')
    @token_required
    @admin_required
    def delete(self, current_user, report_id):
        """删除报表"""
        try:
            report = Report.query.get_or_404(report_id)
            
            # 删除相关的订阅
            ReportSubscription.query.filter_by(report_id=report_id).delete()
            
            db.session.delete(report)
            db.session.commit()
            
            logger.info(f"用户 {current_user.username} 删除了报表: {report.name}")
            return {'message': '报表删除成功'}
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"删除报表失败: {str(e)}")
            api.abort(500, f"删除报表失败: {str(e)}")


@api.route('/reports/<int:report_id>/generate')
class ReportGenerateAPI(Resource):
    @api.doc('生成报表数据')
    @token_required
    @operator_required
    def post(self, current_user, report_id):
        """生成报表数据"""
        try:
            report = Report.query.get_or_404(report_id)
            data = request.get_json() or {}
            
            # 获取日期范围
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                start_date = datetime.now() - timedelta(days=30)
                
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            else:
                end_date = datetime.now()
                
            # 根据报表类型生成数据
            report_data = self._generate_report_data(report, start_date, end_date, data.get('filters', {}))
            
            return {
                'report_id': report_id,
                'report_name': report.name,
                'generated_at': datetime.now().isoformat(),
                'data': report_data,
                'total_records': len(report_data)
            }
            
        except Exception as e:
            logger.error(f"生成报表数据失败: {str(e)}")
            api.abort(500, f"生成报表数据失败: {str(e)}")
    
    def _generate_report_data(self, report, start_date, end_date, filters):
        """根据报表类型生成数据"""
        if report.report_type == 'task_summary':
            return self._generate_task_summary(start_date, end_date, filters)
        elif report.report_type == 'result_analysis':
            return self._generate_result_analysis(start_date, end_date, filters)
        elif report.report_type == 'performance_report':
            return self._generate_performance_report(start_date, end_date, filters)
        else:
            return []
    
    def _generate_task_summary(self, start_date, end_date, filters):
        """生成任务汇总报表"""
        query = Task.query.filter(
            Task.created_at >= start_date,
            Task.created_at <= end_date
        )
        
        if filters.get('status'):
            query = query.filter(Task.status == filters['status'])
            
        tasks = query.all()
        
        return [{
            'id': task.id,
            'name': task.name,
            'status': task.status,
            'created_at': task.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': task.updated_at.strftime('%Y-%m-%d %H:%M:%S') if task.updated_at else '',
            'agent_ids': task.agent_ids or []
        } for task in tasks]
    
    def _generate_result_analysis(self, start_date, end_date, filters):
        """生成结果分析报表"""
        query = Result.query.filter(
            Result.created_at >= start_date,
            Result.created_at <= end_date
        )
        
        if filters.get('task_id'):
            query = query.filter(Result.task_id == filters['task_id'])
            
        results = query.all()
        
        return [{
            'id': result.id,
            'task_id': result.task_id,
            'agent_id': result.agent_id,
            'status': result.status,
            'result_data': result.result_data,
            'created_at': result.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for result in results]
    
    def _generate_performance_report(self, start_date, end_date, filters):
        """生成性能报表"""
        # 这里可以根据实际需求实现性能数据统计
        return [{
            'date': start_date.strftime('%Y-%m-%d'),
            'total_tasks': Task.query.filter(
                Task.created_at >= start_date,
                Task.created_at <= end_date
            ).count(),
            'completed_tasks': Task.query.filter(
                Task.created_at >= start_date,
                Task.created_at <= end_date,
                Task.status == 'completed'
            ).count()
        }]


@api.route('/reports/<int:report_id>/export')
class ReportExportAPI(Resource):
    @api.doc('导出报表')
    @api.expect(export_model)
    @token_required
    @viewer_required
    def post(self, current_user, report_id):
        """导出报表"""
        try:
            report = Report.query.get_or_404(report_id)
            data = request.get_json()
            
            if not data or not data.get('format'):
                api.abort(400, "导出格式不能为空")
                
            export_format = data['format'].lower()
            if export_format not in ['excel', 'pdf']:
                api.abort(400, "不支持的导出格式")
            
            # 获取日期范围
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                start_date = datetime.now() - timedelta(days=30)
                
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            else:
                end_date = datetime.now()
            
            # 生成报表数据
            generate_api = ReportGenerateAPI()
            report_data = generate_api._generate_report_data(
                report, start_date, end_date, data.get('filters', {})
            )
            
            if not report_data:
                api.abort(404, "没有找到符合条件的数据")
            
            # 导出文件
            try:
                if export_format == 'excel':
                    file_stream = ExportUtils.export_to_excel(report_data)
                    mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                else:  # pdf
                    file_stream = ExportUtils.export_to_pdf(report_data, title=report.name)
                    mimetype = 'application/pdf'
                
                filename = ExportUtils.get_export_filename(export_format, report.name)
                
                logger.info(f"用户 {current_user.username} 导出了报表: {report.name} ({export_format})")
                
                return send_file(
                    file_stream,
                    mimetype=mimetype,
                    as_attachment=True,
                    download_name=filename
                )
                
            except ImportError as ie:
                api.abort(500, f"导出功能不可用: {str(ie)}")
            except Exception as ee:
                logger.error(f"导出文件失败: {str(ee)}")
                api.abort(500, f"导出文件失败: {str(ee)}")
                
        except Exception as e:
            logger.error(f"导出报表失败: {str(e)}")
            api.abort(500, f"导出报表失败: {str(e)}")


@api.route('/reports/types')
class ReportTypesAPI(Resource):
    @api.doc('获取报表类型列表')
    @token_required
    @viewer_required
    def get(self, current_user):
        """获取支持的报表类型"""
        return {
            'types': [
                {
                    'value': 'task_summary',
                    'label': '任务汇总报表',
                    'description': '统计任务执行情况'
                },
                {
                    'value': 'result_analysis',
                    'label': '结果分析报表',
                    'description': '分析任务执行结果'
                },
                {
                    'value': 'performance_report',
                    'label': '性能报表',
                    'description': '系统性能统计'
                }
            ]
        }