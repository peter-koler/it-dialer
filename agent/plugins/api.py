#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API拨测插件
实现多步骤API事务监控，包括动态变量传递和灵活的断言验证
"""

import requests
import json
import time
import logging
import re
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone
import os

# 插件名称
PLUGIN_NAME = "api"

# 配置日志
logger = logging.getLogger(__name__)

# 尝试导入jsonpath_ng，如果失败则设置为None
try:
    import jsonpath_ng
    JSONPATH_AVAILABLE = True
except ImportError:
    jsonpath_ng = None
    JSONPATH_AVAILABLE = False
    logger.warning("jsonpath_ng库未安装，JSONPath功能将不可用")


def execute(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    执行API拨测任务
    
    Args:
        task: 任务配置
            {
                "task_id": "task_1",
                "type": "api",
                "target": "https://api.example.com",
                "config": {
                    "variables": [
                        {"name": "$var1", "value": "initial_value"}
                    ],
                    "steps": [
                        {
                            "step_id": "s1",
                            "name": "Step 1: Login",
                            "request": {...},
                            "extract": [...],
                            "assertions": [...]
                        },
                        ...
                    ]
                }
            }
            
    Returns:
        执行结果
    """
    task_id = task.get("task_id", "unknown")
    target = task.get("target", "")
    config = task.get("config", {})
    
    logger.info(f"API任务配置: task_id={task_id}, target={target}, config={json.dumps(config, ensure_ascii=False)}")
    
    if isinstance(config, str):
        try:
            config = json.loads(config)
        except json.JSONDecodeError:
            logger.error(f"任务 {task_id} 的config不是有效的JSON")
            return {
                "status": "failed",
                "response_time": 0,
                "message": "配置解析失败：无效的JSON格式",
                "details": {
                    "error": "配置解析失败：无效的JSON格式"
                }
            }
    
    logger.info(f"开始执行API拨测任务 {task_id}: 目标={target}")
    
    # 初始化执行上下文
    context = {}
    
    # 加载初始变量 - 支持V2格式
    # V2格式：initialVariables
    initial_variables = config.get("initialVariables", [])
    if initial_variables:
        for var in initial_variables:
            name = var.get("name")
            value = var.get("value")
            if name and name.startswith("$"):
                context[name] = value
                logger.debug(f"加载初始变量: {name} = {value}")
    
    # 兼容V1格式：variables
    variables = config.get("variables", [])
    for var in variables:
        name = var.get("name")
        value = var.get("value")
        if name and name.startswith("$"):
            context[name] = value
            logger.debug(f"加载变量: {name} = {value}")
    
    # 从后端获取系统变量 ($public_...)
    system_variables = get_system_variables()
    context.update(system_variables)
    
    # 处理V2认证配置
    authentications = config.get("authentications", [])
    auth_config = None
    if authentications and len(authentications) > 0:
        # 使用第一个认证配置（V2支持多个认证，但目前只使用第一个）
        auth_config = authentications[0]
        logger.debug(f"使用认证配置: {auth_config.get('type', 'unknown')}")
    
    # 准备结果对象
    result = {
        "status": "success",
        "response_time": 0,  # 总耗时
        "message": "",
        "details": {
            "steps": [],
            "variables": {},
            "total_assertions": 0,
            "passed_assertions": 0,
            "start_time": datetime.now().isoformat(),
            "end_time": ""
        }
    }
    
    # 记录初始变量状态
    result["details"]["variables"] = dict(context)
    
    # 开始计时
    start_time = time.time()
    
    # 执行步骤
    steps = config.get("steps", [])
    total_assertions = 0
    passed_assertions = 0
    
    for step in steps:
        # 将认证配置应用到步骤中
        if auth_config:
            if "request" not in step:
                step["request"] = {}
            step["request"]["auth"] = auth_config
        
        step_result = execute_step(step, context)
        result["details"]["steps"].append(step_result)
        
        # 更新断言统计
        step_assertions = len(step_result.get("assertions", []))
        step_passed = sum(1 for a in step_result.get("assertions", []) if a.get("result") == True)
        
        total_assertions += step_assertions
        passed_assertions += step_passed
        
        # 如果步骤失败，标记整个任务为失败
        if step_result.get("status") == "failed":
            logger.warning(f"步骤 {step.get('step_id')} 失败")
            result["status"] = "failed"
            result["message"] = f"步骤 '{step.get('name')}' 失败: {step_result.get('message')}"
            
            # 如果配置为中止，则停止执行
            if step.get("fail_fast", False):
                logger.warning(f"步骤 {step.get('step_id')} 失败，中止执行")
                break
    
    # 计算总耗时
    end_time = time.time()
    total_time = (end_time - start_time) * 1000  # 转换为毫秒
    
    # 更新结果
    result["response_time"] = round(total_time, 2)
    result["details"]["total_assertions"] = total_assertions
    result["details"]["passed_assertions"] = passed_assertions
    result["details"]["end_time"] = datetime.now().isoformat()
    
    # 如果没有明确失败，但有断言失败，也标记为失败
    if result["status"] != "failed" and passed_assertions < total_assertions:
        result["status"] = "failed"
        result["message"] = f"断言失败: {passed_assertions}/{total_assertions} 通过"
    
    # 如果成功完成所有步骤
    if result["status"] == "success":
        completed_steps = len(result["details"]["steps"])
        failed_steps = sum(1 for step in result["details"]["steps"] if step.get("status") == "failed")
        if failed_steps == 0:
            result["message"] = f"成功完成所有 {completed_steps} 个步骤"
        else:
            result["message"] = f"完成 {completed_steps} 个步骤，其中 {failed_steps} 个失败"
    
    # 统计结果摘要
    failed_steps = sum(1 for step in result["details"]["steps"] if step.get("status") == "failed")
    successful_steps = sum(1 for step in result["details"]["steps"] if step.get("status") == "success")
    
    logger.info(f"API拨测任务 {task_id} 执行完成: 状态={result['status']}, 耗时={result['response_time']}ms, 总步骤={len(steps)}, 成功={successful_steps}, 失败={failed_steps}")
    return result


def get_system_variables() -> Dict[str, Any]:
    """
    从后端获取系统变量
    
    Returns:
        系统变量字典
    """
    system_variables = {}
    try:
        # 从环境变量或配置文件获取服务器URL
        server_url = os.environ.get("SERVER_URL", "http://localhost:5000")
        
        # 获取系统变量
        response = requests.get(f"{server_url}/api/v1/system-variables")
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 0:
                variables = data.get("data", {}).get("list", [])
                for var in variables:
                    name = var.get("name")
                    value = var.get("value")
                    if name and name.startswith("$"):
                        system_variables[name] = value
                        logger.debug(f"加载系统变量: {name} = {value}")
            else:
                logger.warning(f"获取系统变量失败: {data.get('message')}")
        else:
            logger.warning(f"获取系统变量HTTP错误: {response.status_code}")
    except Exception as e:
        logger.error(f"获取系统变量时发生异常: {e}")
    
    return system_variables


def execute_step(step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    执行单个API步骤
    
    Args:
        step: 步骤配置
        context: 变量上下文
        
    Returns:
        步骤执行结果
    """
    step_id = step.get("step_id", "unknown")
    step_name = step.get("name", f"Step {step_id}")
    
    logger.info(f"执行步骤: {step_name} (ID: {step_id})")
    
    # 初始化步骤结果
    step_result = {
        "step_id": step_id,
        "name": step_name,
        "status": "success",
        "response_time": 0,
        "message": "",
        "request": {},
        "response": {},
        "assertions": [],
        "extractions": []
    }
    
    try:
        # 获取请求配置
        request_config = step.get("request", {})
        if not request_config:
            raise ValueError("步骤缺少request配置")
        
        # 替换变量
        request_config = replace_variables(request_config, context)
        
        # 记录请求信息（脱敏处理敏感信息）
        step_result["request"] = sanitize_request(request_config)
        
        # 执行请求
        start_time = time.time()
        response = send_request(request_config)
        end_time = time.time()
        
        # 计算响应时间
        response_time = (end_time - start_time) * 1000  # 转换为毫秒
        step_result["response_time"] = round(response_time, 2)
        
        # 记录响应信息
        step_result["response"] = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content_type": response.headers.get("Content-Type", ""),
            "body": get_response_body(response),
            "size": len(response.content)
        }
        
        # 提取变量 - 支持V2格式的variables字段
        extractions = step.get("extract", [])
        variables = step.get("variables", [])
        
        # 处理V2格式的variables配置
        for var_config in variables:
            # 转换V2格式到extract格式
            extraction = {
                "source": var_config.get("source", "body"),  # V2中source可能是"body"
                "expression": var_config.get("expression", ""),
                "variable_name": var_config.get("name", "")  # V2中使用"name"字段
            }
            # 处理source字段的兼容性
            if extraction["source"] == "body":
                extraction["source"] = "json_body"
            
            extract_result = extract_variable(extraction, response, context)
            step_result["extractions"].append(extract_result)
        
        # 处理传统的extract配置
        for extraction in extractions:
            extract_result = extract_variable(extraction, response, context)
            step_result["extractions"].append(extract_result)
        
        # 执行断言
        assertions = step.get("assertions", [])
        all_assertions_passed = True
        
        for assertion in assertions:
            assertion_result = execute_assertion(assertion, response)
            step_result["assertions"].append(assertion_result)
            
            if not assertion_result.get("result"):
                all_assertions_passed = False
        
        # 如果有断言失败，标记步骤为失败
        if not all_assertions_passed:
            step_result["status"] = "failed"
            step_result["message"] = "断言失败"
        else:
            step_result["message"] = "步骤执行成功"
            
    except Exception as e:
        logger.error(f"步骤 {step_id} 执行异常: {str(e)}")
        step_result["status"] = "failed"
        step_result["message"] = f"执行异常: {str(e)}"
        step_result["response_time"] = 0
    
    return step_result


def replace_variables(obj: Any, context: Dict[str, Any]) -> Any:
    """
    递归替换对象中的变量引用
    
    Args:
        obj: 要处理的对象
        context: 变量上下文
        
    Returns:
        替换后的对象
    """
    if isinstance(obj, str):
        # 替换字符串中的所有变量引用
        result = obj
        # 按变量名长度降序排列，优先替换长变量名，避免部分替换问题
        sorted_vars = sorted(context.items(), key=lambda x: len(x[0]), reverse=True)
        for var_name, var_value in sorted_vars:
            # 确保变量名在字符串中存在再进行替换
            if var_name in result:
                # 转义特殊正则字符以避免问题
                escaped_var_name = re.escape(var_name)
                result = re.sub(escaped_var_name, str(var_value), result)
        return result
    elif isinstance(obj, dict):
        return {k: replace_variables(v, context) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_variables(item, context) for item in obj]
    else:
        return obj


def sanitize_request(request_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    对请求配置进行脱敏处理，移除敏感信息
    
    Args:
        request_config: 请求配置
        
    Returns:
        脱敏后的请求配置
    """
    sanitized = dict(request_config)
    
    # 处理认证信息
    if "auth" in sanitized:
        auth = dict(sanitized["auth"])
        if "password" in auth:
            auth["password"] = "******"
        sanitized["auth"] = auth
    
    # 处理敏感头信息
    if "headers" in sanitized and isinstance(sanitized["headers"], list):
        headers = []
        for header in sanitized["headers"]:
            if isinstance(header, dict):
                header_copy = dict(header)
                key = header_copy.get("key", "").lower()
                if key in ["authorization", "x-api-key", "api-key", "token"]:
                    header_copy["value"] = "******"
                headers.append(header_copy)
            else:
                headers.append(header)
        sanitized["headers"] = headers
    
    return sanitized


def send_request(request_config: Dict[str, Any]) -> requests.Response:
    """
    发送HTTP请求
    
    Args:
        request_config: 请求配置
        
    Returns:
        HTTP响应对象
    """
    method = request_config.get("method", "GET")
    url = request_config.get("url", "")
    
    # 准备请求参数
    kwargs = {}
    
    # 处理查询参数
    params = {}
    for param in request_config.get("params", []):
        if isinstance(param, dict) and "key" in param and "value" in param:
            params[param["key"]] = param["value"]
    if params:
        kwargs["params"] = params
    
    # 处理请求头
    headers = {}
    for header in request_config.get("headers", []):
        if isinstance(header, dict) and "key" in header and "value" in header:
            headers[header["key"]] = header["value"]
    if headers:
        kwargs["headers"] = headers
    
    # 处理请求体
    body_config = request_config.get("body", {})
    if body_config and method in ["POST", "PUT", "PATCH"]:
        body_type = body_config.get("type", "json")
        content = body_config.get("content", "")
        
        if body_type == "json" and content:
            try:
                if isinstance(content, str):
                    kwargs["json"] = json.loads(content)
                else:
                    kwargs["json"] = content
            except json.JSONDecodeError:
                # 如果不是有效的JSON，作为原始字符串处理
                kwargs["data"] = content
        elif body_type == "form":
            kwargs["data"] = content
        elif body_type == "text":
            kwargs["data"] = content
    
    # 处理认证
    auth_config = request_config.get("auth", {})
    if auth_config:
        auth_type = auth_config.get("type")
        if auth_type == "basic":
            kwargs["auth"] = (auth_config.get("username", ""), auth_config.get("password", ""))
        elif auth_type == "digest":
            try:
                from requests.auth import HTTPDigestAuth
                kwargs["auth"] = HTTPDigestAuth(auth_config.get("username", ""), auth_config.get("password", ""))
            except ImportError:
                logger.warning("缺少requests库的HTTPDigestAuth支持，无法支持Digest认证")
        elif auth_type == "bearer":
            # Bearer token认证
            token = auth_config.get("token", "")
            if "headers" not in kwargs:
                kwargs["headers"] = {}
            kwargs["headers"]["Authorization"] = f"Bearer {token}"
        elif auth_type == "oauth1":
            # OAuth 1.0认证
            try:
                from requests_oauthlib import OAuth1
                oauth1 = OAuth1(
                    client_key=auth_config.get("consumerKey", ""),
                    client_secret=auth_config.get("consumerSecret", ""),
                    resource_owner_key=auth_config.get("accessToken", ""),
                    resource_owner_secret=auth_config.get("tokenSecret", ""),
                    signature_method=auth_config.get("signatureMethod", "HMAC-SHA1")
                )
                kwargs["auth"] = oauth1
            except ImportError:
                logger.warning("缺少requests-oauthlib库，无法支持OAuth 1.0认证")
        elif auth_type == "oauth2":
            # OAuth 2.0认证 - 使用Access Token
            access_token = auth_config.get("accessToken", "")
            if access_token:
                if "headers" not in kwargs:
                    kwargs["headers"] = {}
                kwargs["headers"]["Authorization"] = f"Bearer {access_token}"
    
    # 处理SSL选项
    kwargs["verify"] = request_config.get("ssl_verify", True)
    if "ssl_cert" in request_config:
        cert_file = request_config["ssl_cert"]
        cert_key = request_config.get("ssl_key")
        if cert_key:
            kwargs["cert"] = (cert_file, cert_key)
        else:
            kwargs["cert"] = cert_file
    
    # 设置超时
    timeout_config = request_config.get("timeout", 30)
    if isinstance(timeout_config, dict):
        kwargs["timeout"] = (
            timeout_config.get("connect", 30),
            timeout_config.get("read", 30)
        )
    else:
        kwargs["timeout"] = timeout_config
    
    # 设置允许的HTTP方法
    allowed_methods = request_config.get("allowed_methods")
    if allowed_methods:
        kwargs["method_whitelist"] = allowed_methods
    
    # 发送请求
    response = requests.request(method, url, **kwargs)
    return response


def get_response_body(response: requests.Response) -> Any:
    """
    获取响应体，尝试解析为JSON，如果失败则返回文本
    
    Args:
        response: HTTP响应对象
        
    Returns:
        解析后的响应体
    """
    try:
        return response.json()
    except ValueError:
        return response.text


def extract_variable(extraction: Dict[str, Any], response: requests.Response, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    从响应中提取变量
    
    Args:
        extraction: 提取配置
        response: HTTP响应对象
        context: 变量上下文
        
    Returns:
        提取结果
    """
    source = extraction.get("source", "json_body")
    expression = extraction.get("expression", "")
    variable_name = extraction.get("variable_name", "")
    
    if not variable_name or not variable_name.startswith("$"):
        return {
            "source": source,
            "expression": expression,
            "variable_name": variable_name,
            "success": False,
            "message": "变量名无效，必须以$开头"
        }
    
    result = {
        "source": source,
        "expression": expression,
        "variable_name": variable_name,
        "success": False,
        "message": "",
        "value": None
    }
    
    try:
        # 根据来源获取数据
        data = None
        if source == "json_body":
            try:
                data = response.json()
            except ValueError:
                result["message"] = "响应不是有效的JSON格式"
                return result
        elif source == "text_body":
            data = response.text
        elif source == "headers":
            data = dict(response.headers)
        elif source == "status_code":
            data = response.status_code
            # 直接将状态码赋值给变量
            context[variable_name] = data
            result["success"] = True
            result["value"] = data
            result["message"] = "成功提取状态码"
            return result
        else:
            result["message"] = f"不支持的数据源: {source}"
            return result
        
        # 使用表达式提取数据
        if source == "json_body":
            # 使用JSONPath提取
            if not JSONPATH_AVAILABLE:
                result["message"] = "未安装jsonpath_ng库，无法使用JSONPath提取功能"
                return result
                
            try:
                jsonpath_expr = jsonpath_ng.parse(expression)
                matches = [match.value for match in jsonpath_expr.find(data)]
                
                if matches:
                    # 使用第一个匹配项
                    value = matches[0]
                    context[variable_name] = value
                    result["success"] = True
                    result["value"] = value
                    result["message"] = "成功提取变量"
                else:
                    result["message"] = f"JSONPath表达式未匹配到任何数据: {expression}"
            except Exception as e:
                result["message"] = f"JSONPath表达式错误: {str(e)}"
        elif source == "text_body" and expression:
            # 使用正则表达式提取
            try:
                match = re.search(expression, data)
                if match:
                    value = match.group(1) if match.groups() else match.group(0)
                    context[variable_name] = value
                    result["success"] = True
                    result["value"] = value
                    result["message"] = "成功提取变量"
                else:
                    result["message"] = f"正则表达式未匹配到任何数据: {expression}"
            except Exception as e:
                result["message"] = f"正则表达式错误: {str(e)}"
        elif source == "headers" and expression:
            # 直接获取指定的头信息
            value = data.get(expression)
            if value is not None:
                context[variable_name] = value
                result["success"] = True
                result["value"] = value
                result["message"] = "成功提取头信息"
            else:
                result["message"] = f"未找到指定的头信息: {expression}"
    except Exception as e:
        result["message"] = f"提取变量时发生异常: {str(e)}"
    
    return result


def execute_assertion(assertion: Dict[str, Any], response: requests.Response) -> Dict[str, Any]:
    """
    执行断言
    
    Args:
        assertion: 断言配置
        response: HTTP响应对象
        
    Returns:
        断言结果
    """
    source = assertion.get("source", "status_code")
    comparison = assertion.get("comparison", "equal")
    target = assertion.get("target")
    property_path = assertion.get("property", "")
    
    result = {
        "source": source,
        "comparison": comparison,
        "target": target,
        "property": property_path,
        "result": False,
        "message": "",
        "actual_value": None
    }
    
    try:
        # 获取实际值
        actual = None
        
        if source == "status_code":
            actual = response.status_code
        elif source == "json_body":
            try:
                data = response.json()
                if property_path:
                    # 使用JSONPath获取属性
                    if not JSONPATH_AVAILABLE:
                        result["message"] = "未安装jsonpath_ng库，无法使用JSONPath功能"
                        return result
                        
                    try:
                        jsonpath_expr = jsonpath_ng.parse(property_path)
                        matches = [match.value for match in jsonpath_expr.find(data)]
                        if matches:
                            actual = matches[0]
                        else:
                            result["message"] = f"JSONPath表达式未匹配到任何数据: {property_path}"
                            return result
                    except Exception as e:
                        result["message"] = f"JSONPath表达式错误: {str(e)}"
                        return result
                else:
                    actual = data
            except ValueError:
                result["message"] = "响应不是有效的JSON格式"
                return result
        elif source == "text_body":
            actual = response.text
        elif source == "headers":
            if property_path:
                actual = response.headers.get(property_path)
                if actual is None:
                    result["message"] = f"未找到指定的头信息: {property_path}"
                    return result
            else:
                actual = dict(response.headers)
        else:
            result["message"] = f"不支持的数据源: {source}"
            return result
        
        result["actual_value"] = actual
        
        # 执行比较
        if comparison == "equal":
            result["result"] = actual == target
        elif comparison == "not_equal":
            result["result"] = actual != target
        elif comparison == "greater_than":
            result["result"] = actual > target
        elif comparison == "less_than":
            result["result"] = actual < target
        elif comparison == "contains":
            if isinstance(actual, str):
                result["result"] = target in actual
            elif isinstance(actual, (list, dict)):
                result["result"] = target in actual
            else:
                result["result"] = False
                result["message"] = f"不支持的数据类型进行contains比较: {type(actual)}"
        elif comparison == "not_contains":
            if isinstance(actual, str):
                result["result"] = target not in actual
            elif isinstance(actual, (list, dict)):
                result["result"] = target not in actual
            else:
                result["result"] = False
                result["message"] = f"不支持的数据类型进行not_contains比较: {type(actual)}"
        elif comparison == "exists":
            result["result"] = actual is not None
        elif comparison == "not_exists":
            result["result"] = actual is None
        elif comparison == "empty":
            if isinstance(actual, (str, list, dict)):
                result["result"] = len(actual) == 0
            else:
                result["result"] = actual is None
        elif comparison == "not_empty":
            if isinstance(actual, (str, list, dict)):
                result["result"] = len(actual) > 0
            else:
                result["result"] = actual is not None
        elif comparison == "matches":
            if isinstance(actual, str) and isinstance(target, str):
                result["result"] = bool(re.search(target, actual))
            else:
                result["result"] = False
                result["message"] = "matches比较要求实际值和目标值都是字符串"
        else:
            result["message"] = f"不支持的比较操作: {comparison}"
            return result
        
        # 设置结果消息
        if result["result"]:
            result["message"] = "断言通过"
        else:
            result["message"] = f"断言失败: 期望 {actual} {comparison} {target}"
        
        # 检查是否需要触发告警
        enable_alert = assertion.get("enableAlert", False)
        if enable_alert:
            alert_condition = assertion.get("alertCondition", "match")
            should_trigger_alert = False
            
            if alert_condition == "match" and result["result"]:
                # 断言匹配时告警
                should_trigger_alert = True
            elif alert_condition == "not_match" and not result["result"]:
                # 断言不匹配时告警
                should_trigger_alert = True
            
            if should_trigger_alert:
                # 触发告警
                alert_info = {
                    "type": "assertion_alert",
                    "source": source,
                    "property": property_path,
                    "comparison": comparison,
                    "expected": target,
                    "actual": actual,
                    "condition": alert_condition,
                    "message": f"断言告警触发: {result['message']}",
                    "timestamp": datetime.now().isoformat()
                }
                result["alert"] = alert_info
                logger.warning(f"断言告警触发: {alert_info['message']}")
            
    except Exception as e:
        result["message"] = f"执行断言时发生异常: {str(e)}"
    
    return result