from flask import request, jsonify
import traceback
import re
from datetime import datetime
from . import v2_bp as bp
from app import db
from app.models.system_variable import SystemVariable
from app.utils.auth_decorators import token_required
from app.utils.tenant_context import TenantContext, tenant_required, check_resource_limit


@bp.route('/system-variables', methods=['GET'])
@token_required
@tenant_required
def get_system_variables_v2():
    """获取系统变量列表 - v2版本（强制租户隔离）"""
    try:
        # 获取当前租户ID
        tenant_id = TenantContext.get_current_tenant_id()
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        keyword = request.args.get('keyword', type=str)
        
        # 构建查询，强制租户过滤
        query = SystemVariable.query.filter(SystemVariable.tenant_id == tenant_id)
        
        # 默认过滤掉已删除的变量
        include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
        if not include_deleted:
            query = query.filter(SystemVariable.is_deleted == False)
        
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
        
        # 按创建时间倒序排列
        query = query.order_by(SystemVariable.created_at.desc())
        
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
                'total': pagination.total,
                'page': page,
                'size': size
            },
            'message': 'ok'
        })
    except Exception as e:
        print(f"Error in get_system_variables_v2: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'code': 1,
            'message': f'获取系统变量失败: {str(e)}'
        }), 500


@bp.route('/system-variables/deleted', methods=['GET'])
@token_required
@tenant_required
def get_deleted_system_variables_v2():
    """获取已删除的系统变量列表 - v2版本（强制租户隔离）"""
    try:
        # 获取当前租户ID
        tenant_id = TenantContext.get_current_tenant_id()
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        keyword = request.args.get('keyword', type=str)
        
        # 构建查询，强制租户过滤，只查询已删除的变量
        query = SystemVariable.query.filter(
            SystemVariable.tenant_id == tenant_id,
            SystemVariable.is_deleted == True
        )
        
        # 应用搜索条件
        if keyword:
            search = f"%{keyword}%"
            query = query.filter(
                db.or_(
                    SystemVariable.name.like(search),
                    SystemVariable.description.like(search)
                )
            )
        
        # 按删除时间倒序排列
        query = query.order_by(SystemVariable.deleted_at.desc())
        
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
                'total': pagination.total,
                'page': page,
                'size': size
            },
            'message': 'ok'
        })
    except Exception as e:
        print(f"Error in get_deleted_system_variables_v2: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'code': 1,
            'message': f'获取已删除系统变量失败: {str(e)}'
        }), 500


@bp.route('/system-variables', methods=['POST'])
@token_required
@tenant_required
@check_resource_limit('variables')
def create_system_variable_v2():
    """创建系统变量 - v2版本（强制租户隔离）"""
    try:
        # 获取当前租户ID
        tenant_id = TenantContext.get_current_tenant_id()
        
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
        
        # 检查变量名是否已存在（在当前租户中）
        existing_var = SystemVariable.query.filter(
            SystemVariable.tenant_id == tenant_id,
            SystemVariable.name == data['name'],
            SystemVariable.is_deleted == False
        ).first()
        
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
            is_secret=data.get('is_secret', False),
            tenant_id=tenant_id  # 强制设置租户ID
        )
        
        db.session.add(new_var)
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': new_var.to_dict(),
            'message': '系统变量创建成功'
        }), 201
    except Exception as e:
        print(f"Error in create_system_variable_v2: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'code': 1,
            'message': f'创建系统变量失败: {str(e)}'
        }), 500


@bp.route('/system-variables/<int:var_id>', methods=['GET'])
@token_required
@tenant_required
def get_system_variable_v2(var_id):
    """获取单个系统变量 - v2版本（强制租户隔离）"""
    try:
        # 获取当前租户ID
        tenant_id = TenantContext.get_current_tenant_id()
        
        var = SystemVariable.query.filter(
            SystemVariable.id == var_id,
            SystemVariable.tenant_id == tenant_id,
            SystemVariable.is_deleted == False
        ).first()
        
        if not var:
            return jsonify({
                'code': 1,
                'message': f'系统变量不存在或无权限访问: ID {var_id}'
            }), 404
        
        return jsonify({
            'code': 0,
            'data': var.to_dict(),
            'message': 'ok'
        })
    except Exception as e:
        print(f"Error in get_system_variable_v2: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'code': 1,
            'message': f'获取系统变量失败: {str(e)}'
        }), 500


@bp.route('/system-variables/<int:var_id>', methods=['PUT'])
@token_required
@tenant_required
def update_system_variable_v2(var_id):
    """更新系统变量 - v2版本（强制租户隔离）"""
    try:
        # 获取当前租户ID
        tenant_id = TenantContext.get_current_tenant_id()
        
        var = SystemVariable.query.filter(
            SystemVariable.id == var_id,
            SystemVariable.tenant_id == tenant_id,
            SystemVariable.is_deleted == False
        ).first()
        
        if not var:
            return jsonify({
                'code': 1,
                'message': f'系统变量不存在或无权限访问: ID {var_id}'
            }), 404
        
        data = request.get_json()
        
        # 如果要更新变量名，需要验证格式和唯一性
        if 'name' in data and data['name'] != var.name:
            # 验证变量名格式
            if not re.match(r'^\$[a-zA-Z][a-zA-Z0-9_]*$', data['name']):
                return jsonify({
                    'code': 1,
                    'message': '变量名格式不正确，必须以$开头，后跟字母、数字或下划线'
                }), 400
            
            # 检查新变量名是否已存在（在当前租户中）
            existing_var = SystemVariable.query.filter(
                SystemVariable.tenant_id == tenant_id,
                SystemVariable.name == data['name'],
                SystemVariable.is_deleted == False,
                SystemVariable.id != var_id
            ).first()
            
            if existing_var:
                return jsonify({
                    'code': 1,
                    'message': f'变量名 {data["name"]} 已存在'
                }), 400
        
        # 更新字段
        if 'name' in data:
            var.name = data['name']
        if 'value' in data:
            var.value = data['value']
        if 'description' in data:
            var.description = data['description']
        if 'is_secret' in data:
            var.is_secret = data['is_secret']
        
        var.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': var.to_dict(),
            'message': '系统变量更新成功'
        })
    except Exception as e:
        print(f"Error in update_system_variable_v2: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'code': 1,
            'message': f'更新系统变量失败: {str(e)}'
        }), 500


@bp.route('/system-variables/<int:var_id>', methods=['DELETE'])
@token_required
@tenant_required
def delete_system_variable_v2(var_id):
    """删除系统变量 - v2版本（强制租户隔离）"""
    try:
        # 获取当前租户ID
        tenant_id = TenantContext.get_current_tenant_id()
        
        var = SystemVariable.query.filter(
            SystemVariable.id == var_id,
            SystemVariable.tenant_id == tenant_id,
            SystemVariable.is_deleted == False
        ).first()
        
        if not var:
            return jsonify({
                'code': 1,
                'message': f'系统变量不存在或无权限访问: ID {var_id}'
            }), 404
        
        # 软删除
        var.is_deleted = True
        var.deleted_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'message': '系统变量删除成功'
        })
    except Exception as e:
        print(f"Error in delete_system_variable_v2: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'code': 1,
            'message': f'删除系统变量失败: {str(e)}'
        }), 500


@bp.route('/system-variables/<int:var_id>/restore', methods=['POST'])
@token_required
@tenant_required
def restore_system_variable_v2(var_id):
    """恢复已删除的系统变量 - v2版本（强制租户隔离）"""
    try:
        # 获取当前租户ID
        tenant_id = TenantContext.get_current_tenant_id()
        
        var = SystemVariable.query.filter(
            SystemVariable.id == var_id,
            SystemVariable.tenant_id == tenant_id,
            SystemVariable.is_deleted == True
        ).first()
        
        if not var:
            return jsonify({
                'code': 1,
                'message': f'已删除的系统变量不存在或无权限访问: ID {var_id}'
            }), 404
        
        # 检查变量名是否与现有变量冲突
        existing_var = SystemVariable.query.filter(
            SystemVariable.tenant_id == tenant_id,
            SystemVariable.name == var.name,
            SystemVariable.is_deleted == False
        ).first()
        
        if existing_var:
            return jsonify({
                'code': 1,
                'message': f'无法恢复，变量名 {var.name} 已存在'
            }), 400
        
        # 恢复变量
        var.is_deleted = False
        var.deleted_at = None
        var.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'data': var.to_dict(),
            'message': '系统变量恢复成功'
        })
    except Exception as e:
        print(f"Error in restore_system_variable_v2: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'code': 1,
            'message': f'恢复系统变量失败: {str(e)}'
        }), 500