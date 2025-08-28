from flask import request, jsonify
from . import bp
from app import db
from app.models.result import Result
from app.models.task import Task
from app.services.alert_matcher import alert_matcher
from app.utils.auth_decorators import token_required
from app.utils.tenant_context import get_current_tenant_id, filter_by_tenant, add_tenant_id
import json
from datetime import datetime
import traceback
from dateutil import parser


@bp.route('/results', methods=['GET'])
@token_required
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
        
        # 构建查询，由于Agent现在是全局共享资源，只过滤当前租户的任务
        query = Result.query.join(Task).filter(Task.tenant_id == get_current_tenant_id())
        
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
        print(f"Error in get_results: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'获取结果列表失败: {str(e)}'
        }), 500


# TCP拨测点相关API端点
@bp.route('/tasks/<int:task_id>/tcp/probes/<location>/<agent_area>/detail', methods=['GET'])
def get_tcp_probe_detail(task_id, location, agent_area):
    """获取TCP拨测点详情"""
    try:
        # 检查任务是否存在且为tcp类型
        task = Task.query.get(task_id)
        if not task:
            return jsonify({
                'code': 404,
                'data': {},
                'message': f'任务 ID {task_id} 不存在'
            }), 404
        
        if task.type != 'tcp':
            return jsonify({
                'code': 400,
                'data': {},
                'message': f'任务类型不是tcp: {task.type}'
            }), 400
        
        # 检查是否为实时数据请求
        realtime = request.args.get('realtime', 'false').lower() == 'true'
        
        if realtime:
            # 获取最新的拨测结果
            latest_result = Result.query.filter_by(
                task_id=task_id,
                agent_area=agent_area
            ).order_by(Result.created_at.desc()).first()
            
            if not latest_result:
                return jsonify({
                    'code': 404,
                    'data': {},
                    'message': '未找到实时数据'
                }), 404
            
            return jsonify({
                'code': 0,
                'data': latest_result.to_dict(),
                'message': 'ok'
            })
        else:
            # 获取拨测点基本信息
            return jsonify({
                'code': 0,
                'data': {
                    'task_id': task_id,
                    'task_name': task.name,
                    'target': task.target,
                    'location': location,
                    'agent_area': agent_area,
                    'type': task.type,
                    'interval': task.interval,
                    'enabled': task.enabled
                },
                'message': 'ok'
            })
    except Exception as e:
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'获取TCP拨测点详情失败: {str(e)}'
        }), 500


@bp.route('/tasks/<int:task_id>/tcp/probes/<location>/<agent_area>/trend', methods=['GET'])
def get_tcp_probe_trend(task_id, location, agent_area):
    """获取TCP拨测点趋势数据"""
    try:
        # 检查任务是否存在且为tcp类型
        task = Task.query.get(task_id)
        if not task:
            return jsonify({
                'code': 404,
                'data': {},
                'message': f'任务 ID {task_id} 不存在'
            }), 404
        
        if task.type != 'tcp':
            return jsonify({
                'code': 400,
                'data': {},
                'message': f'任务类型不是tcp: {task.type}'
            }), 400
        
        # 获取时间范围参数
        hours = int(request.args.get('hours', 24))
        
        # 查询指定时间范围内的拨测结果
        from datetime import datetime, timedelta
        start_time = datetime.now() - timedelta(hours=hours)
        
        results = Result.query.filter(
            Result.task_id == task_id,
            Result.agent_area == agent_area,
            Result.created_at >= start_time
        ).order_by(Result.created_at.asc()).all()
        
        # 构建趋势数据
        trend_data = {
            'response_time': [],
            'success_rate': [],
            'timestamps': []
        }
        
        for result in results:
            result_dict = result.to_dict()
            trend_data['timestamps'].append(result_dict['created_at'])
            
            # TCP连接时间
            if result_dict.get('status') == 'success':
                response_time = result_dict.get('response_time', 0)
                trend_data['response_time'].append(response_time)
                trend_data['success_rate'].append(100)
            else:
                trend_data['response_time'].append(None)
                trend_data['success_rate'].append(0)
        
        return jsonify({
            'code': 0,
            'data': trend_data,
            'message': 'ok'
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'获取TCP拨测点趋势数据失败: {str(e)}'
        }), 500


@bp.route('/tasks/<int:task_id>/tcp/probes/<location>/<agent_area>/records', methods=['GET'])
def get_tcp_probe_records(task_id, location, agent_area):
    """获取TCP拨测点记录"""
    try:
        # 检查任务是否存在且为tcp类型
        task = Task.query.get(task_id)
        if not task:
            return jsonify({
                'code': 404,
                'data': {},
                'message': f'任务 ID {task_id} 不存在'
            }), 404
        
        if task.type != 'tcp':
            return jsonify({
                'code': 400,
                'data': {},
                'message': f'任务类型不是tcp: {task.type}'
            }), 400
        
        # 获取分页参数
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 20))
        
        # 查询拨测记录
        query = Result.query.filter_by(
            task_id=task_id,
            agent_area=agent_area
        ).order_by(Result.created_at.desc())
        
        # 分页查询
        pagination = query.paginate(
            page=page,
            per_page=size,
            error_out=False
        )
        
        records = [result.to_dict() for result in pagination.items]
        
        return jsonify({
            'code': 0,
            'data': {
                'records': records,
                'total': pagination.total,
                'page': page,
                'size': size,
                'pages': pagination.pages
            },
            'message': 'ok'
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'获取TCP拨测点记录失败: {str(e)}'
        }), 500


# Ping拨测点相关API端点
@bp.route('/tasks/<int:task_id>/ping/probes/<location>/<agent_area>/detail', methods=['GET'])
def get_ping_probe_detail(task_id, location, agent_area):
    """获取Ping拨测点详情"""
    try:
        # 检查任务是否存在且为ping类型
        task = Task.query.get(task_id)
        if not task:
            return jsonify({
                'code': 404,
                'data': {},
                'message': f'任务 ID {task_id} 不存在'
            }), 404
        
        if task.type != 'ping':
            return jsonify({
                'code': 400,
                'data': {},
                'message': f'任务类型不是ping: {task.type}'
            }), 400
        
        # 检查是否为实时数据请求
        realtime = request.args.get('realtime', 'false').lower() == 'true'
        
        if realtime:
            # 获取最新的拨测结果
            latest_result = Result.query.filter_by(
                task_id=task_id,
                agent_area=agent_area
            ).order_by(Result.created_at.desc()).first()
            
            if not latest_result:
                return jsonify({
                    'code': 404,
                    'data': {},
                    'message': '未找到实时数据'
                }), 404
            
            return jsonify({
                'code': 0,
                'data': latest_result.to_dict(),
                'message': 'ok'
            })
        else:
            # 获取拨测点基本信息
            return jsonify({
                'code': 0,
                'data': {
                    'task_id': task_id,
                    'task_name': task.name,
                    'target': task.target,
                    'location': location,
                    'agent_area': agent_area,
                    'type': task.type,
                    'interval': task.interval,
                    'enabled': task.enabled
                },
                'message': 'ok'
            })
    except Exception as e:
        print(f"Error in get_ping_probe_detail: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'获取拨测点详情失败: {str(e)}'
        }), 500


@bp.route('/tasks/<int:task_id>/ping/probes/<location>/<agent_area>/trend', methods=['GET'])
def get_ping_probe_trend(task_id, location, agent_area):
    """获取Ping拨测点历史趋势数据"""
    try:
        # 检查任务是否存在且为ping类型
        task = Task.query.get(task_id)
        if not task:
            return jsonify({
                'code': 404,
                'data': {},
                'message': f'任务 ID {task_id} 不存在'
            }), 404
        
        if task.type != 'ping':
            return jsonify({
                'code': 400,
                'data': {},
                'message': f'任务类型不是ping: {task.type}'
            }), 400
        
        # 获取查询参数
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        
        # 构建查询
        query = Result.query.filter_by(
            task_id=task_id,
            agent_area=agent_area
        )
        
        # 应用时间范围过滤
        if start_time:
            try:
                start_dt = parser.isoparse(start_time)
                query = query.filter(Result.created_at >= start_dt)
            except (ValueError, TypeError) as e:
                print(f"Error parsing start_time: {e}")
        
        if end_time:
            try:
                end_dt = parser.isoparse(end_time)
                query = query.filter(Result.created_at <= end_dt)
            except (ValueError, TypeError) as e:
                print(f"Error parsing end_time: {e}")
        
        # 按时间排序
        results = query.order_by(Result.created_at.asc()).all()
        
        # 转换为趋势数据格式
        trend_data = []
        for result in results:
            try:
                result_dict = result.to_dict()
                trend_data.append({
                    'timestamp': result_dict['created_at'],
                    'response_time': result_dict.get('response_time', 0),
                    'status': result_dict.get('status', 'unknown'),
                    'packet_loss': result_dict.get('details', {}).get('packet_loss', 0) if result_dict.get('details') else 0
                })
            except Exception as e:
                print(f"Error processing result {result.id}: {e}")
                continue
        
        return jsonify({
            'code': 0,
            'data': trend_data,
            'message': 'ok'
        })
    except Exception as e:
        print(f"Error in get_ping_probe_trend: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'获取趋势数据失败: {str(e)}'
        }), 500


@bp.route('/tasks/<int:task_id>/ping/probes/<location>/<agent_area>/records', methods=['GET'])
def get_ping_probe_records(task_id, location, agent_area):
    """获取Ping拨测点详细记录"""
    try:
        # 检查任务是否存在且为ping类型
        task = Task.query.get(task_id)
        if not task:
            return jsonify({
                'code': 404,
                'data': {},
                'message': f'任务 ID {task_id} 不存在'
            }), 404
        
        if task.type != 'ping':
            return jsonify({
                'code': 400,
                'data': {},
                'message': f'任务类型不是ping: {task.type}'
            }), 400
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        
        # 构建查询
        query = Result.query.filter_by(
            task_id=task_id,
            agent_area=agent_area
        )
        
        # 应用时间范围过滤
        if start_time:
            try:
                start_dt = parser.isoparse(start_time)
                query = query.filter(Result.created_at >= start_dt)
            except (ValueError, TypeError) as e:
                print(f"Error parsing start_time: {e}")
        
        if end_time:
            try:
                end_dt = parser.isoparse(end_time)
                query = query.filter(Result.created_at <= end_dt)
            except (ValueError, TypeError) as e:
                print(f"Error parsing end_time: {e}")
        
        # 按创建时间倒序排列
        query = query.order_by(Result.created_at.desc())
        
        # 应用分页
        pagination = query.paginate(
            page=page,
            per_page=page_size,
            error_out=False
        )
        
        results = pagination.items
        
        # 转换为字典列表
        records_data = []
        for result in results:
            try:
                records_data.append(result.to_dict())
            except Exception as e:
                print(f"Error converting result {result.id} to dict: {str(e)}")
                continue
        
        return jsonify({
            'code': 0,
            'data': {
                'list': records_data,
                'total': pagination.total,
                'page': page,
                'page_size': page_size
            },
            'message': 'ok'
        })
    except Exception as e:
        print(f"Error in get_ping_probe_records: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'获取记录数据失败: {str(e)}'
        }), 500


# Ping记录详情API端点
@bp.route('/ping/records/<int:record_id>', methods=['GET'])
def get_ping_record_detail(record_id):
    """获取Ping记录详情"""
    try:
        result = Result.query.get(record_id)
        if not result:
            return jsonify({
                'code': 404,
                'data': {},
                'message': f'记录 ID {record_id} 不存在'
            }), 404
        
        # 检查是否为ping类型的结果
        task = Task.query.get(result.task_id)
        if task and task.type != 'ping':
            return jsonify({
                'code': 400,
                'data': {},
                'message': f'记录不是ping类型: {task.type}'
            }), 400
        
        # 构建详细的ping记录数据
        record_data = result.to_dict()
        
        # 添加ping特有的字段
        details = {}
        if result.details:
            try:
                details = json.loads(result.details) if isinstance(result.details, str) else result.details
            except (json.JSONDecodeError, TypeError):
                details = {}
        
        # 构建ping记录详情响应
        ping_detail = {
            'id': result.id,
            'timestamp': result.created_at.isoformat() if result.created_at else None,
            'target': details.get('target') or task.target if task else 'N/A',
            'responseTime': result.response_time or details.get('response_time') or details.get('execution_time') or details.get('rtt_avg') or 0,
            'status': result.status,
            'packetSize': details.get('packet_size') or details.get('size') or 32,
            'ttl': details.get('ttl') or 64,
            'sequence': details.get('sequence') or details.get('seq') or 0,
            'packetLoss': details.get('packet_loss') or 0,
            'errorMessage': result.message or details.get('error_message') or '',
            'sourceIp': details.get('source_ip') or 'N/A',
            'destinationIp': details.get('destination_ip') or details.get('target') or (task.target if task else 'N/A'),
            'protocol': 'ICMP',
            'jitter': details.get('jitter') or 0,
            'route': details.get('route') or []
        }
        
        return jsonify({
            'code': 0,
            'data': ping_detail,
            'message': 'ok'
        })
    except Exception as e:
        print(f"Error in get_ping_record_detail: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'获取ping记录详情失败: {str(e)}'
        }), 500


@bp.route('/results/<int:result_id>', methods=['GET'])
@token_required
def get_result(result_id):
    """Get a specific result by ID"""
    try:
        # 通过关联任务表添加租户过滤
        result = Result.query.join(Task).filter(
            Result.id == result_id,
            Task.tenant_id == get_current_tenant_id()
        ).first()
        if not result:
            return jsonify({
                'code': 404,
                'data': {},
                'message': '结果不存在或无权限访问'
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
        
        # 注意：由于Agent现在是全局共享资源，不再验证租户权限
        # Agent可以为任何租户的任务上报结果
        
        # 创建新结果
        result = Result(
            task_id=data.get('task_id'),
            status=data.get('status'),
            response_time=data.get('response_time'),
            message=data.get('message'),
            details=json.dumps(data.get('details', {})) if data.get('details') else None,
            agent_id=data.get('agent_id'),
            agent_area=data.get('agent_area'),
            tenant_id=data.get('tenant_id')  # 从Agent上报数据中获取tenant_id
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
        
        # 处理告警匹配
        try:
            print(f"[DEBUG] 开始处理告警匹配 - 任务ID: {task.id}, 任务名称: {task.name}, 任务类型: {task.type}")
            print(f"[DEBUG] Agent上报数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            # 检查任务是否有告警配置
            if task.type == 'http':
                alarm_config = task.get_alarm_config()
                print(f"[DEBUG] HTTP任务告警配置: {json.dumps(alarm_config, ensure_ascii=False, indent=2) if alarm_config else 'None'}")
            elif task.type == 'tcp':
                alarm_config = task.get_alarm_config()
                print(f"[DEBUG] TCP任务告警配置: {json.dumps(alarm_config, ensure_ascii=False, indent=2) if alarm_config else 'None'}")
            elif task.type == 'ping':
                alarm_config = task.get_alarm_config()
                print(f"[DEBUG] Ping任务告警配置: {json.dumps(alarm_config, ensure_ascii=False, indent=2) if alarm_config else 'None'}")
            
            alerts = alert_matcher.process_result(data, task)
            
            if alerts:
                print(f"[DEBUG] 成功处理告警匹配，生成了 {len(alerts)} 个告警:")
                for i, alert in enumerate(alerts):
                    print(f"[DEBUG] 告警 {i+1}: 类型={alert.alert_type}, 级别={alert.alert_level}, 标题={alert.title}")
                    print(f"[DEBUG] 告警内容: {alert.content}")
                    print(f"[DEBUG] 触发值: {alert.trigger_value}, 阈值: {alert.threshold_value}")
            else:
                print(f"[DEBUG] 告警匹配处理完成，未生成告警 - 任务ID: {task.id}")
                
        except Exception as e:
            # 告警处理失败不影响结果保存
            print(f"[ERROR] 告警匹配处理失败 - 任务ID: {task.id}, 错误: {str(e)}")
            print(f"[ERROR] 异常堆栈: {traceback.format_exc()}")
        
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


@bp.route('/tasks/<int:task_id>/results/aggregated', methods=['GET'])
def get_aggregated_results(task_id):
    """Get aggregated results for a specific task"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        result_type = request.args.get('type', type=str)
        start_time = request.args.get('start', type=str)
        end_time = request.args.get('end', type=str)
        
        # 检查任务是否存在
        task = Task.query.get(task_id)
        if not task:
            return jsonify({
                'code': 404,
                'data': {},
                'message': f'任务 ID {task_id} 不存在'
            }), 404
        
        # 构建查询
        query = Result.query.filter_by(task_id=task_id)
        
        # 应用类型过滤（如果指定了type参数）
        if result_type:
            # 这里可以根据需要添加类型过滤逻辑
            pass
            
        # 应用时间范围过滤
        if start_time:
            try:
                start_dt = parser.isoparse(start_time)
                query = query.filter(Result.created_at >= start_dt)
            except (ValueError, TypeError) as e:
                print(f"Error parsing start_time: {e}")
                pass
        
        if end_time:
            try:
                end_dt = parser.isoparse(end_time)
                query = query.filter(Result.created_at <= end_dt)
            except (ValueError, TypeError) as e:
                print(f"Error parsing end_time: {e}")
                pass
        
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
        results_data = []
        for result in results:
            try:
                results_data.append(result.to_dict())
            except Exception as e:
                print(f"Error converting result {result.id} to dict: {str(e)}")
                continue
        
        # 计算聚合统计信息
        total_results = pagination.total
        success_count = query.filter_by(status='success').count()
        failed_count = query.filter_by(status='failed').count()
        
        # 计算成功率
        success_rate = (success_count / total_results * 100) if total_results > 0 else 0
        
        # 计算平均响应时间
        avg_response_time = 0
        if results:
            response_times = [r.response_time for r in results if r.response_time is not None]
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
        
        return jsonify({
            'code': 0,
            'data': {
                'list': results_data,
                'total': total_results,
                'pagination': {
                    'page': page,
                    'size': size,
                    'total': total_results
                },
                'statistics': {
                    'total_count': total_results,
                    'success_count': success_count,
                    'failed_count': failed_count,
                    'success_rate': round(success_rate, 2),
                    'avg_response_time': round(avg_response_time, 2)
                }
            },
            'message': 'ok'
        })
    except Exception as e:
        print(f"Error in get_aggregated_results: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'code': 500,
            'data': {},
            'message': f'获取聚合结果失败: {str(e)}'
        }), 500