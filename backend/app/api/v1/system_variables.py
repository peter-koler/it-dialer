from flask import request, jsonify
import traceback
import re
from . import bp
from app import db
from app.models.system_variable import SystemVariable


@bp.route('/system-variables', methods=['GET'])
@bp.route('/system/variables', methods=['GET'])
def get_system_variables():
    """获取所有系统变量"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        keyword = request.args.get('keyword', type=str)
        
        # 构建查询
        query = SystemVariable.query
        
        # 应用过滤条件
        if keyword:
            # 搜索变量名或描述
            search = f"%{keyword}%"
            query = query.filter(
                db.or_(
                    SystemVariable.name.like(search),
                    SystemVariable.description.like(search)
                )
            )
        
        # 应用分页
        pagination = query.paginate(
            page=page, 
            per_page=size, 
            error_out=False
        )
        
        variables = pagination.items
        
        # 转换为字典列表
        variables_data = [var.to_dict() for var in variables]
        
        return jsonify({
            'code': 0,
            'data': {
                'list': variables_data,
                'total': pagination.total
            },
            'message': 'ok'
        })
    except Exception as e:
        print(f"Error in get_system_variables: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'code': 1,
            'message': f'获取系统变量失败: {str(e)}'
        }), 500


@bp.route('/system-variables', methods=['POST'])
@bp.route('/system/variables', methods=['POST'])
def create_system_variable():
    """创建系统变量"""
    try:
        data = request.get_json()
        
        # 验证必要字段
        required_fields = ['name', 'value', 'description']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'code': 1,
                    'message': f'缺少必要字段: {field}'
                }), 400
        
        # 验证变量名格式
        if not re.match(r'^\$[a-zA-Z][a-zA-Z0-9_]*$', data['name']):
            return jsonify({
                'code': 1,
                'message': '变量名格式不正确，必须以$开头，后跟字母、数字或下划线'
            }), 400
        
        # 检查变量名是否已存在
        existing_var = SystemVariable.query.filter_by(name=data['name']).first()
        if existing_var:
            return jsonify({
                'code': 1,
                'message': f'变量名 {data["name"]} 已存在'
            }), 400
        
        # 创建新变量
        new_var = SystemVariable(
            name=data['name'],
            value=data['value'],
            description=data['description'],
            is_secret=data.get('is_secret', False)
        )
        
        db.session.add(new_var)
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': new_var.to_dict(),
            'message': '系统变量创建成功'
        }), 201
    except Exception as e:
        print(f"Error in create_system_variable: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'code': 1,
            'message': f'创建系统变量失败: {str(e)}'
        }), 500


@bp.route('/system-variables/<int:var_id>', methods=['GET'])
@bp.route('/system/variables/<int:var_id>', methods=['GET'])
def get_system_variable(var_id):
    """获取单个系统变量"""
    try:
        var = SystemVariable.query.get(var_id)
        if not var:
            return jsonify({
                'code': 1,
                'message': f'系统变量不存在: ID {var_id}'
            }), 404
        
        return jsonify({
            'code': 0,
            'data': var.to_dict(),
            'message': 'ok'
        })
    except Exception as e:
        print(f"Error in get_system_variable: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'code': 1,
            'message': f'获取系统变量失败: {str(e)}'
        }), 500


@bp.route('/system-variables/<int:var_id>', methods=['PUT'])
@bp.route('/system/variables/<int:var_id>', methods=['PUT'])
def update_system_variable(var_id):
    """更新系统变量"""
    try:
        var = SystemVariable.query.get(var_id)
        if not var:
            return jsonify({
                'code': 1,
                'message': f'系统变量不存在: ID {var_id}'
            }), 404
        
        data = request.get_json()
        
        # 如果更新变量名，验证格式和唯一性
        if 'name' in data and data['name'] != var.name:
            if not re.match(r'^\$[a-zA-Z][a-zA-Z0-9_]*$', data['name']):
                return jsonify({
                    'code': 1,
                    'message': '变量名格式不正确，必须以$开头，后跟字母、数字或下划线'
                }), 400
            
            existing_var = SystemVariable.query.filter_by(name=data['name']).first()
            if existing_var:
                return jsonify({
                    'code': 1,
                    'message': f'变量名 {data["name"]} 已存在'
                }), 400
            
            var.name = data['name']
        
        # 更新其他字段
        if 'value' in data:
            var.value = data['value']
        if 'description' in data:
            var.description = data['description']
        if 'is_secret' in data:
            var.is_secret = data['is_secret']
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': var.to_dict(),
            'message': '系统变量更新成功'
        })
    except Exception as e:
        print(f"Error in update_system_variable: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'code': 1,
            'message': f'更新系统变量失败: {str(e)}'
        }), 500


@bp.route('/system-variables/<int:var_id>', methods=['DELETE'])
@bp.route('/system/variables/<int:var_id>', methods=['DELETE'])
def delete_system_variable(var_id):
    """删除系统变量"""
    try:
        var = SystemVariable.query.get(var_id)
        if not var:
            return jsonify({
                'code': 1,
                'message': f'系统变量不存在: ID {var_id}'
            }), 404
        
        db.session.delete(var)
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'message': '系统变量删除成功'
        })
    except Exception as e:
        print(f"Error in delete_system_variable: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'code': 1,
            'message': f'删除系统变量失败: {str(e)}'
        }), 500