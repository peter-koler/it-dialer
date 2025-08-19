from flask import request, jsonify
from . import bp
from app import db
from app.models.result import Result
from app.models.task import Task
import json
from datetime import datetime
import traceback
from dateutil import parser


@bp.route('/results', methods=['GET'])
def get_results():
    """Get all results"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        task_id = request.args.get('task_id', type=int)
        status = request.args.get('status', type=str)
        start_time = request.args.get('start', type=str)
        end_time = request.args.get('end', type=str)
        
        # 构建查询
        query = Result.query
        
        # 应用过滤条件
        if task_id is not None:
            query = query.filter_by(task_id=task_id)
        
        if status:
            query = query.filter_by(status=status)
            
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
        print(f"Error in get_results: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'获取结果列表失败: {str(e)}'
        }), 500


@bp.route('/results/<int:result_id>', methods=['GET'])
def get_result(result_id):
    """Get a specific result by ID"""
    try:
        result = Result.query.get(result_id)
        if not result:
            return jsonify({
                'code': 404,
                'data': {},
                'message': f'结果 ID {result_id} 不存在'
            }), 404
        
        return jsonify({
            'code': 0,
            'data': result.to_dict(),
            'message': 'ok'
        })
    except Exception as e:
        print(f"Error in get_result: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'获取结果详情失败: {str(e)}'
        }), 500


@bp.route('/results', methods=['POST'])
def create_result():
    """Create a new result"""
    try:
        data = request.get_json()
        
        # 检查任务是否存在，并处理API任务的特殊结果格式
        # API任务的details字段需要包含多步骤的详细信息
        task = Task.query.get(data.get('task_id'))
        if not task:
            return jsonify({
                'code': 400,
                'data': {},
                'message': '任务不存在'
            }), 400
        
        # 创建新结果
        result = Result(
            task_id=data.get('task_id'),
            status=data.get('status'),
            response_time=data.get('response_time'),
            message=data.get('message'),
            details=json.dumps(data.get('details', {})) if data.get('details') else None,
            agent_id=data.get('agent_id'),
            agent_area=data.get('agent_area')
        )
        
        # 如果客户端提供了created_at，则使用客户端提供的时间
        if 'created_at' in data and data['created_at']:
            try:
                # 解析客户端提供的时间
                created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
                result.created_at = created_at
            except Exception as e:
                # 如果解析失败，使用默认时间
                pass
        
        # 保存到数据库
        db.session.add(result)
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': result.to_dict(),
            'message': '结果创建成功'
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error in create_result: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'创建结果失败: {str(e)}'
        }), 500