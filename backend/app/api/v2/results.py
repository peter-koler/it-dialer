from flask import request, jsonify
from ..v2 import v2_bp as bp
from app import db
from app.models.result import Result
from app.models.task import Task
from app.utils.auth_decorators import token_required
from app.utils.tenant_context import TenantContext
import json
from datetime import datetime
import traceback
from dateutil import parser


@bp.route('/results', methods=['GET'])
@token_required
def get_results_v2():
    """Get all results with tenant isolation"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        task_id = request.args.get('task_id', type=int)
        status = request.args.get('status', type=str)
        start_time = request.args.get('start', type=str)
        end_time = request.args.get('end', type=str)
        
        # 构建查询，根据用户角色决定是否进行租户过滤
        if TenantContext.is_super_admin():
            # 超级管理员可以查看所有租户的结果
            query = Result.query.join(Task)
        else:
            # 普通用户只能查看自己租户的结果
            tenant_id = TenantContext.get_current_tenant_id()
            if not tenant_id:
                return jsonify({
                    'code': 403,
                    'data': {},
                    'message': '缺少租户信息'
                }), 403
            query = Result.query.join(Task).filter(Task.tenant_id == tenant_id)
        
        # 应用过滤条件
        if task_id is not None:
            query = query.filter(Result.task_id == task_id)
        
        if status:
            query = query.filter(Result.status == status)
            
        # 应用时间范围过滤
        if start_time:
            try:
                # 使用dateutil.parser可以更好地处理各种时间格式
                start_dt = parser.isoparse(start_time)
                query = query.filter(Result.created_at >= start_dt)
            except (ValueError, TypeError) as e:
                print(f"Error parsing start_time: {e}")
                pass  # 如果时间格式不正确，忽略该过滤条件
        
        if end_time:
            try:
                # 使用dateutil.parser可以更好地处理各种时间格式
                end_dt = parser.isoparse(end_time)
                query = query.filter(Result.created_at <= end_dt)
            except (ValueError, TypeError) as e:
                print(f"Error parsing end_time: {e}")
                pass  # 如果时间格式不正确，忽略该过滤条件
        
        # 按创建时间倒序排列
        query = query.order_by(Result.created_at.desc())
        
        # 应用分页
        pagination = query.paginate(
            page=page, 
            per_page=size, 
            error_out=False
        )
        
        results = pagination.items
        
        # 转换为字典列表，并添加单个转换失败时的日志记录
        results_data = []
        for result in results:
            try:
                results_data.append(result.to_dict())
            except Exception as e:
                print(f"Error converting result {result.id} to dict: {str(e)}")
                print(traceback.format_exc())
                # 即使单个结果转换失败，也继续处理其他结果
                continue
        
        return jsonify({
            'code': 0,
            'data': {
                'list': results_data,
                'total': pagination.total
            },
            'message': 'ok'
        })
    except Exception as e:
        print(f"Error in get_results_v2: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'获取结果列表失败: {str(e)}'
        }), 500


@bp.route('/results/<int:result_id>', methods=['GET'])
@token_required
def get_result_v2(result_id):
    """Get a single result with tenant isolation"""
    try:
        # 根据用户角色决定是否进行租户过滤
        if TenantContext.is_super_admin():
            # 超级管理员可以查看所有租户的结果
            result = Result.query.join(Task).filter(Result.id == result_id).first()
        else:
            # 普通用户只能查看自己租户的结果
            tenant_id = TenantContext.get_current_tenant_id()
            if not tenant_id:
                return jsonify({
                    'code': 403,
                    'data': {},
                    'message': '缺少租户信息'
                }), 403
            result = Result.query.join(Task).filter(
                Result.id == result_id,
                Task.tenant_id == tenant_id
            ).first()
        
        if not result:
            return jsonify({
                'code': 404,
                'data': {},
                'message': '结果不存在'
            }), 404
        
        return jsonify({
            'code': 0,
            'data': result.to_dict(),
            'message': 'ok'
        })
    except Exception as e:
        print(f"Error in get_result_v2: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'获取结果详情失败: {str(e)}'
        }), 500