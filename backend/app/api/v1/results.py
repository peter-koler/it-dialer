from flask import request, jsonify
from . import bp
from app import db
from app.models.result import Result
from app.models.task import Task
import json
from datetime import datetime


@bp.route('/results', methods=['GET'])
def get_results():
    """Get all results"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        task_id = request.args.get('task_id', type=int)
        status = request.args.get('status', type=str)
        
        # 构建查询
        query = Result.query
        
        # 应用过滤条件
        if task_id is not None:
            query = query.filter_by(task_id=task_id)
        
        if status:
            query = query.filter_by(status=status)
        
        # 按创建时间倒序排列
        query = query.order_by(Result.created_at.desc())
        
        # 应用分页
        pagination = query.paginate(
            page=page, 
            per_page=size, 
            error_out=False
        )
        
        results = pagination.items
        
        # 转换为字典列表
        results_data = [result.to_dict() for result in results]
        
        return jsonify({
            'code': 0,
            'data': {
                'list': results_data,
                'total': pagination.total
            },
            'message': 'ok'
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'获取结果列表失败: {str(e)}'
        }), 500


@bp.route('/results', methods=['POST'])
def create_result():
    """Create a new result"""
    try:
        data = request.get_json()
        
        # 检查任务是否存在
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
            details=json.dumps(data.get('details', {})) if data.get('details') else None
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
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'创建结果失败: {str(e)}'
        }), 500