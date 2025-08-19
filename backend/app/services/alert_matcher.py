from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import re
from app import db
from app.models.alert import Alert, AlertConfig
from app.models.task import Task
from app.models.result import Result
import logging

logger = logging.getLogger(__name__)


class AlertMatcher:
    """
    告警匹配服务
    负责根据agent上报的API步骤数据进行告警规则匹配
    """
    
    def __init__(self):
        self.logger = logger
    
    def process_result(self, result_data: Dict[str, Any], task: Task) -> List[Alert]:
        """
        处理agent上报的结果数据，检查是否触发告警
        
        Args:
            result_data: agent上报的结果数据
            task: 任务对象
            
        Returns:
            List[Alert]: 生成的告警列表
        """
        alerts = []
        
        try:
            self.logger.info(f"开始处理任务告警匹配 - 任务ID: {task.id}, 任务名称: {task.name}")
            self.logger.info(f"Agent上报数据: {result_data}")
            
            # 获取任务配置
            task_config = task.get_config()
            self.logger.info(f"任务配置: {task_config}")
            
            # 获取任务的告警配置
            alert_configs = AlertConfig.query.filter_by(
                task_id=task.id,
                enabled=True
            ).all()
            
            self.logger.info(f"找到 {len(alert_configs)} 个启用的告警配置")
            
            # 即使没有AlertConfig配置，也要检查任务配置告警
            # if not alert_configs:
            #     return alerts
            
            # 解析结果详情
            details = result_data.get('details', {})
            if isinstance(details, str):
                try:
                    details = json.loads(details)
                except json.JSONDecodeError:
                    details = {}
            
            # 检查API任务的步骤数据
            if task.type == 'api' and 'steps' in details:
                api_alerts = self._check_api_steps_alerts(
                    details['steps'], 
                    alert_configs, 
                    result_data, 
                    task
                )
                self.logger.info(f"API步骤告警检查结果: {len(api_alerts)} 个告警")
                alerts.extend(api_alerts)
            
            # 检查全局告警（响应时间等）
            global_alerts = self._check_global_alerts(
                result_data, 
                alert_configs, 
                task
            )
            self.logger.info(f"全局告警检查结果: {len(global_alerts)} 个告警")
            alerts.extend(global_alerts)
            
            # 检查任务状态告警和超时告警（基于任务配置）
            task_config_alerts = self._check_task_config_alerts(
                result_data,
                task
            )
            self.logger.info(f"任务配置告警检查结果: {len(task_config_alerts)} 个告警")
            alerts.extend(task_config_alerts)
            
            self.logger.info(f"总共生成 {len(alerts)} 个告警")
            for i, alert in enumerate(alerts):
                self.logger.info(f"告警 {i+1}: 类型={alert.alert_type}, 级别={alert.alert_level}, 标题={alert.title}")
            
        except Exception as e:
            self.logger.error(f"处理告警匹配时发生异常: {str(e)}")
            import traceback
            self.logger.error(f"异常堆栈: {traceback.format_exc()}")
        
        return alerts
    
    def _check_api_steps_alerts(self, steps: List[Dict], alert_configs: List[AlertConfig], 
                               result_data: Dict, task: Task) -> List[Alert]:
        """
        检查API步骤的告警
        
        Args:
            steps: API步骤执行结果列表
            alert_configs: 告警配置列表
            result_data: 完整的结果数据
            task: 任务对象
            
        Returns:
            List[Alert]: 生成的告警列表
        """
        alerts = []
        
        # 获取任务配置中的步骤定义
        task_config = task.get_config() or {}
        api_steps = task_config.get('apiSteps', [])
        
        for step in steps:
            step_id = step.get('step_id', '')
            
            # 从任务配置中找到对应的步骤定义
            step_config = None
            for api_step in api_steps:
                if api_step.get('id') == step_id:
                    step_config = api_step
                    break
            
            if not step_config:
                continue
                
            # 检查状态码告警
            alerts_config = step_config.get('alerts', {})
            if alerts_config.get('allowedStatusCodes'):
                alert = self._check_step_status_code_alert(
                    step, step_config, result_data, task, step_id
                )
                if alert:
                    alerts.append(alert)
            
            # 检查响应时间告警
            if alerts_config.get('responseTimeThreshold', 0) > 0:
                alert = self._check_step_response_time_alert(
                    step, step_config, result_data, task, step_id
                )
                if alert:
                    alerts.append(alert)
            
            # 检查断言告警
            assertion_alerts = self._check_step_assertion_alerts(
                step, step_config, result_data, task, step_id
            )
            alerts.extend(assertion_alerts)
        
        return alerts
    
    def _check_step_status_code_alert(self, step: Dict, step_config: Dict, result_data: Dict, 
                                     task: Task, step_id: str) -> Optional[Alert]:
        """
        检查步骤状态码告警（从步骤配置中读取告警级别）
        """
        try:
            status_code = step.get('response', {}).get('status_code')
            if status_code is None:
                return None
            
            alerts_config = step_config.get('alerts', {})
            allowed_codes_str = alerts_config.get('allowedStatusCodes', '200')
            alert_level = alerts_config.get('statusCodeAlertLevel', 'warning')
            
            # 解析允许的状态码
            allowed_codes = []
            for code_str in allowed_codes_str.split(','):
                code_str = code_str.strip()
                if code_str.endswith('xx'):
                    # 处理2xx, 3xx等格式
                    prefix = int(code_str[0])
                    allowed_codes.extend(range(prefix * 100, (prefix + 1) * 100))
                else:
                    try:
                        allowed_codes.append(int(code_str))
                    except ValueError:
                        continue
            
            if status_code not in allowed_codes:
                return self._create_alert(
                    task=task,
                    step_id=step_id,
                    alert_type='status_code',
                    alert_level=alert_level,
                    title=f'步骤 {step_id} 状态码异常',
                    content=f'状态码 {status_code} 不在允许范围 {allowed_codes_str} 内',
                    trigger_value=str(status_code),
                    threshold_value=allowed_codes_str,
                    result_data=result_data
                )
            
        except Exception as e:
            self.logger.error(f"检查步骤状态码告警时发生异常: {str(e)}")
        
        return None
    
    def _check_step_response_time_alert(self, step: Dict, step_config: Dict, result_data: Dict, 
                                       task: Task, step_id: str) -> Optional[Alert]:
        """
        检查步骤响应时间告警（从步骤配置中读取告警级别）
        """
        try:
            response_time = step.get('response_time', 0)
            alerts_config = step_config.get('alerts', {})
            threshold = alerts_config.get('responseTimeThreshold', 0)
            alert_level = alerts_config.get('responseTimeAlertLevel', 'warning')
            
            # 将阈值从秒转换为毫秒进行比较
            threshold_ms = threshold * 1000
            response_time_ms = response_time * 1000 if response_time < 100 else response_time
            
            if response_time_ms > threshold_ms:
                return self._create_alert(
                    task=task,
                    step_id=step_id,
                    alert_type='response_time',
                    alert_level=alert_level,
                    title=f'步骤 {step_id} 响应时间超时',
                    content=f'响应时间 {response_time_ms:.2f}ms 超过阈值 {threshold_ms:.2f}ms',
                    trigger_value=f'{response_time_ms:.2f}ms',
                    threshold_value=f'{threshold_ms:.2f}ms',
                    result_data=result_data
                )
            
        except Exception as e:
            self.logger.error(f"检查步骤响应时间告警时发生异常: {str(e)}")
        
        return None
    
    def _check_step_assertion_alerts(self, step: Dict, step_config: Dict, result_data: Dict, 
                                    task: Task, step_id: str) -> List[Alert]:
        """
        检查步骤断言告警（从步骤配置中读取告警级别）
        """
        alerts = []
        
        try:
            # 从步骤配置中获取断言定义
            assertions_config = step_config.get('assertions', [])
            # 从执行结果中获取断言结果
            assertions_result = step.get('assertions', [])
            
            for i, assertion_config in enumerate(assertions_config):
                if not assertion_config.get('enableAlert', False):
                    continue
                
                # 获取对应的断言结果
                assertion_result = None
                if i < len(assertions_result):
                    assertion_result = assertions_result[i]
                
                if assertion_result is None:
                    continue
                
                result_passed = assertion_result.get('result', True)
                alert_condition = assertion_config.get('alertCondition', 'not_match')
                alert_level = assertion_config.get('alertLevel', 'warning')
                
                should_alert = False
                if alert_condition == 'match' and result_passed:
                    should_alert = True
                elif alert_condition == 'not_match' and not result_passed:
                    should_alert = True
                
                if should_alert:
                    alert = self._create_alert(
                        task=task,
                        step_id=step_id,
                        alert_type='assertion',
                        alert_level=alert_level,
                        title=f'步骤 {step_id} 断言告警',
                        content=assertion_result.get('message', '断言条件触发告警'),
                        trigger_value=str(assertion_result.get('actual', '')),
                        threshold_value=str(assertion_result.get('expected', '')),
                        result_data=result_data
                    )
                    alerts.append(alert)
        
        except Exception as e:
            self.logger.error(f"检查步骤断言告警时发生异常: {str(e)}")
        
        return alerts
    
    def _check_task_config_alerts(self, result_data: Dict, task: Task) -> List[Alert]:
        """
        检查基于任务配置的告警（任务状态告警和超时告警）
        
        Args:
            result_data: agent上报的结果数据
            task: 任务对象
            
        Returns:
            List[Alert]: 生成的告警列表
        """
        alerts = []
        
        try:
            self.logger.info(f"开始检查任务配置告警 - 任务ID: {task.id}")
            
            # 获取任务配置
            config = task.get_config()
            self.logger.info(f"任务配置内容: {config}")
            
            if not config:
                self.logger.info("任务配置为空，跳过任务配置告警检查")
                return alerts
            
            # 检查任务状态告警
            status_alert_config = config.get('statusAlertConfig', [])
            self.logger.info(f"状态告警配置: {status_alert_config}")
            
            if status_alert_config:
                self.logger.info(f"开始检查任务状态告警，配置: {status_alert_config}")
                status_alert = self._check_task_status_alert(
                    result_data, task, status_alert_config
                )
                if status_alert:
                    self.logger.info(f"生成任务状态告警: {status_alert.title}")
                    alerts.append(status_alert)
                else:
                    self.logger.info("未触发任务状态告警")
            else:
                self.logger.info("未配置任务状态告警")
            
            # 检查超时告警
            timeout_alert_enabled = config.get('timeoutAlertEnabled', False)
            self.logger.info(f"超时告警启用状态: {timeout_alert_enabled}")
            
            if timeout_alert_enabled:
                self.logger.info("开始检查任务超时告警")
                timeout_alert = self._check_task_timeout_alert(
                    result_data, task, config
                )
                if timeout_alert:
                    self.logger.info(f"生成任务超时告警: {timeout_alert.title}")
                    alerts.append(timeout_alert)
                else:
                    self.logger.info("未触发任务超时告警")
            else:
                self.logger.info("未启用任务超时告警")
                    
        except Exception as e:
            self.logger.error(f"检查任务配置告警时发生异常: {str(e)}")
            import traceback
            self.logger.error(f"异常堆栈: {traceback.format_exc()}")
        
        return alerts
    
    def _check_global_alerts(self, result_data: Dict, alert_configs: List[AlertConfig], 
                           task: Task) -> List[Alert]:
        """
        检查全局告警（如整体响应时间）
        
        Args:
            result_data: 结果数据
            alert_configs: 告警配置列表
            task: 任务对象
            
        Returns:
            List[Alert]: 生成的告警列表
        """
        alerts = []
        
        # 获取全局告警配置（step_id为None的配置）
        global_configs = [config for config in alert_configs if config.step_id is None]
        
        for config in global_configs:
            config_data = config.get_config()
            
            # 检查全局响应时间告警
            if config.alert_type == 'response_time':
                response_time = result_data.get('response_time', 0)
                threshold = config_data.get('threshold', 0)
                
                if response_time > threshold:
                    alert = self._create_alert(
                        task=task,
                        alert_type='response_time',
                        alert_level=config_data.get('level', 'warning'),
                        title=f'任务 {task.name} 响应时间超时',
                        content=f'响应时间 {response_time}ms 超过阈值 {threshold}ms',
                        trigger_value=str(response_time),
                        threshold_value=str(threshold),
                        result_data=result_data
                    )
                    alerts.append(alert)
        
        return alerts
    
    def _check_status_code_alert(self, step: Dict, config: Dict, result_data: Dict, 
                                task: Task, step_id: str) -> Optional[Alert]:
        """
        检查状态码告警
        
        Args:
            step: 步骤数据
            config: 告警配置
            result_data: 结果数据
            task: 任务对象
            step_id: 步骤ID
            
        Returns:
            Optional[Alert]: 告警对象或None
        """
        try:
            status_code = step.get('response', {}).get('status_code')
            if status_code is None:
                return None
            
            # 获取允许的状态码范围
            allowed_codes = config.get('allowed_codes', [200])
            min_code = config.get('min_code')
            max_code = config.get('max_code')
            
            is_alert = False
            alert_message = ""
            
            # 检查是否在允许的状态码列表中
            if allowed_codes and status_code not in allowed_codes:
                is_alert = True
                alert_message = f"状态码 {status_code} 不在允许范围 {allowed_codes} 内"
            
            # 检查状态码范围
            elif min_code is not None and max_code is not None:
                if status_code < min_code or status_code > max_code:
                    is_alert = True
                    alert_message = f"状态码 {status_code} 不在允许范围 {min_code}-{max_code} 内"
            
            if is_alert:
                return self._create_alert(
                    task=task,
                    step_id=step_id,
                    alert_type='status_code',
                    alert_level=config.get('level', 'warning'),
                    title=f'步骤 {step_id} 状态码异常',
                    content=alert_message,
                    trigger_value=str(status_code),
                    threshold_value=str(allowed_codes or f"{min_code}-{max_code}"),
                    result_data=result_data
                )
            
        except Exception as e:
            self.logger.error(f"检查状态码告警时发生异常: {str(e)}")
        
        return None
    
    def _check_response_time_alert(self, step: Dict, config: Dict, result_data: Dict, 
                                  task: Task, step_id: str) -> Optional[Alert]:
        """
        检查响应时间告警
        
        Args:
            step: 步骤数据
            config: 告警配置
            result_data: 结果数据
            task: 任务对象
            step_id: 步骤ID
            
        Returns:
            Optional[Alert]: 告警对象或None
        """
        try:
            response_time = step.get('response_time', 0)
            threshold = config.get('threshold', 0)
            
            if response_time > threshold:
                return self._create_alert(
                    task=task,
                    step_id=step_id,
                    alert_type='response_time',
                    alert_level=config.get('level', 'warning'),
                    title=f'步骤 {step_id} 响应时间超时',
                    content=f'响应时间 {response_time}ms 超过阈值 {threshold}ms',
                    trigger_value=str(response_time),
                    threshold_value=str(threshold),
                    result_data=result_data
                )
            
        except Exception as e:
            self.logger.error(f"检查响应时间告警时发生异常: {str(e)}")
        
        return None
    
    def _check_assertion_alerts(self, step: Dict, config: Dict, result_data: Dict, 
                               task: Task, step_id: str) -> List[Alert]:
        """
        检查断言告警
        
        Args:
            step: 步骤数据
            config: 告警配置
            result_data: 结果数据
            task: 任务对象
            step_id: 步骤ID
            
        Returns:
            List[Alert]: 告警列表
        """
        alerts = []
        
        try:
            assertions = step.get('assertions', [])
            
            for assertion in assertions:
                # 检查断言是否启用了告警
                if not assertion.get('enableAlert', False):
                    continue
                
                assertion_result = assertion.get('result', True)
                alert_condition = assertion.get('alertCondition', 'not_match')
                
                should_alert = False
                if alert_condition == 'match' and assertion_result:
                    should_alert = True
                elif alert_condition == 'not_match' and not assertion_result:
                    should_alert = True
                
                if should_alert:
                    alert = self._create_alert(
                        task=task,
                        step_id=step_id,
                        alert_type='assertion',
                        alert_level=config.get('level', 'warning'),
                        title=f'步骤 {step_id} 断言告警',
                        content=assertion.get('message', '断言条件触发告警'),
                        trigger_value=str(assertion.get('actual', '')),
                        threshold_value=str(assertion.get('expected', '')),
                        result_data=result_data
                    )
                    alerts.append(alert)
        
        except Exception as e:
            self.logger.error(f"检查断言告警时发生异常: {str(e)}")
        
        return alerts
    
    def _check_task_status_alert(self, result_data: Dict, task: Task, 
                                status_alert_config: List[str]) -> Optional[Alert]:
        """
        检查任务状态告警
        
        Args:
            result_data: agent上报的结果数据
            task: 任务对象
            status_alert_config: 状态告警配置列表（如['failed', 'success']）
            
        Returns:
            Optional[Alert]: 告警对象或None
        """
        try:
            self.logger.info(f"检查任务状态告警 - 任务ID: {task.id}")
            
            # 获取任务状态
            task_status = result_data.get('status')
            self.logger.info(f"Agent上报的任务状态: {task_status}")
            self.logger.info(f"状态告警配置: {status_alert_config}")
            
            if not task_status:
                self.logger.info("Agent上报数据中没有status字段，跳过状态告警检查")
                return None
            
            # 检查是否需要告警
            if task_status in status_alert_config:
                self.logger.info(f"任务状态 '{task_status}' 匹配告警配置，开始生成告警")
                
                # 从任务配置中获取告警级别，如果没有配置则使用默认值
                config = task.get_config()
                alert_level = config.get('statusAlertLevel', 'warning') if config else 'warning'
                # 兼容旧的逻辑：如果是failed状态且没有配置级别，则使用critical
                if task_status == 'failed' and not config.get('statusAlertLevel'):
                    alert_level = 'critical'
                
                title = f"任务状态告警 - {task.name}"
                content = f"任务执行状态为 {task_status}，触发告警。"
                
                # 如果有错误消息，添加到内容中
                if 'message' in result_data:
                    content += f" 错误信息: {result_data['message']}"
                
                alert = self._create_alert(
                    task=task,
                    alert_type='task_status',
                    alert_level=alert_level,
                    title=title,
                    content=content,
                    trigger_value=task_status,
                    threshold_value=','.join(status_alert_config),
                    result_data=result_data
                )
                
                self.logger.info(f"成功创建任务状态告警: {alert.title}")
                return alert
            else:
                self.logger.info(f"任务状态 '{task_status}' 不在告警配置 {status_alert_config} 中，不触发告警")
                
        except Exception as e:
            self.logger.error(f"检查任务状态告警时发生异常: {str(e)}")
            import traceback
            self.logger.error(f"异常堆栈: {traceback.format_exc()}")
        
        return None
    
    def _check_task_timeout_alert(self, result_data: Dict, task: Task, 
                                 config: Dict) -> Optional[Alert]:
        """
        检查任务超时告警
        
        Args:
            result_data: agent上报的结果数据
            task: 任务对象
            config: 任务配置
            
        Returns:
            Optional[Alert]: 告警对象或None
        """
        try:
            # 获取响应时间和超时阈值
            response_time = result_data.get('response_time')
            timeout_threshold = config.get('timeoutThreshold', 5000)  # 默认5秒
            
            if response_time is None:
                return None
            
            # 将响应时间转换为毫秒（如果是秒）
            response_time_ms = response_time * 1000 if response_time < 100 else response_time
            
            # 检查是否超时
            if response_time_ms > timeout_threshold:
                # 从任务配置中获取告警级别，如果没有配置则使用默认值
                alert_level = config.get('timeoutAlertLevel', 'warning')
                
                title = f"任务超时告警 - {task.name}"
                content = f"任务响应时间 {response_time_ms:.2f}ms 超过阈值 {timeout_threshold}ms，触发告警。"
                
                return self._create_alert(
                    task=task,
                    alert_type='task_timeout',
                    alert_level=alert_level,
                    title=title,
                    content=content,
                    trigger_value=f"{response_time_ms:.2f}ms",
                    threshold_value=f"{timeout_threshold}ms",
                    result_data=result_data
                )
                
        except Exception as e:
            self.logger.error(f"检查任务超时告警时发生异常: {str(e)}")
        
        return None
    
    def _create_alert(self, task: Task, alert_type: str, alert_level: str, 
                     title: str, content: str, trigger_value: str = None, 
                     threshold_value: str = None, step_id: str = None, 
                     result_data: Dict = None) -> Alert:
        """
        创建告警对象
        
        Args:
            task: 任务对象
            alert_type: 告警类型
            alert_level: 告警级别
            title: 告警标题
            content: 告警内容
            trigger_value: 触发值
            threshold_value: 阈值
            step_id: 步骤ID
            result_data: 结果数据
            
        Returns:
            Alert: 告警对象
        """
        try:
            self.logger.info(f"开始创建告警 - 任务ID: {task.id}, 类型: {alert_type}, 级别: {alert_level}")
            self.logger.info(f"告警标题: {title}")
            self.logger.info(f"告警内容: {content}")
            
            alert = Alert(
                task_id=task.id,
                step_id=step_id,
                alert_type=alert_type,
                alert_level=alert_level,
                title=title,
                content=content,
                trigger_value=trigger_value,
                threshold_value=threshold_value,
                agent_id=result_data.get('agent_id') if result_data else None,
                agent_area=result_data.get('agent_area') if result_data else None
            )
            
            # 设置快照数据
            if result_data:
                snapshot_data = {
                    'task_name': task.name,
                    'step_id': step_id,
                    'trigger_time': datetime.utcnow().isoformat(),
                    'result_data': result_data
                }
                alert.set_snapshot_data(snapshot_data)
                self.logger.info(f"设置告警快照数据: {len(str(result_data))} 字符")
            
            # 保存到数据库
            db.session.add(alert)
            db.session.commit()
            
            self.logger.info(f"告警成功保存到数据库 - 告警ID: {alert.id}, 类型: {alert_type}, 级别: {alert_level}")
            
            return alert
            
        except Exception as e:
            self.logger.error(f"创建告警时发生异常: {str(e)}")
            import traceback
            self.logger.error(f"异常堆栈: {traceback.format_exc()}")
            raise
    
    def save_alerts(self, alerts: List[Alert]) -> None:
        """
        保存告警到数据库
        
        Args:
            alerts: 告警列表
        """
        try:
            for alert in alerts:
                db.session.add(alert)
            db.session.commit()
            
            if alerts:
                self.logger.info(f"成功保存 {len(alerts)} 条告警")
                
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"保存告警时发生异常: {str(e)}")
            raise


# 全局告警匹配器实例
alert_matcher = AlertMatcher()