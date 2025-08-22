#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HTTP插件
实现HTTP/HTTPS拨测任务，支持DNS解析时间、连接时间、SSL握手时间、首字节时间、下载时间等指标
"""

import requests
import time
import socket
import ssl
import logging
import json
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import dns.resolver
import dns.exception
from datetime import datetime, timezone
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 插件名称
PLUGIN_NAME = "http"

# 配置日志
logger = logging.getLogger(__name__)

def execute(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    执行HTTP拨测任务
    
    Args:
        task: 任务配置
            {
                "task_id": "task_1",
                "type": "http",
                "target": "https://www.baidu.com",
                "params": {
                    "method": "GET",
                    "timeout": 30,
                    "headers": {},
                    "follow_redirects": True
                }
            }
            
    Returns:
        执行结果
    """
    target = task.get("target", "")
    params = task.get("params", {})
    task_id = task.get("task_id", "unknown")
    
    logger.info(f"开始执行HTTP任务 {task_id}: 目标={target}")
    
    if not target:
        return {
            "status": "failed",
            "response_time": 0,
            "message": "目标URL不能为空",
            "webstatus": "异常",
            "details": {
                "error": "目标URL不能为空"
            }
        }
    
    try:
        # 解析URL
        parsed_url = urlparse(target)
        if not parsed_url.scheme:
            target = "http://" + target
            parsed_url = urlparse(target)
        
        hostname = parsed_url.hostname
        port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
        is_https = parsed_url.scheme == 'https'
        
        # 获取参数
        method = params.get("method", "GET").upper()
        timeout = params.get("timeout", 30)
        headers = params.get("headers", {})
        follow_redirects = params.get("follow_redirects", True)
        
        # 开始计时
        start_time = time.time()
        
        # 1. DNS解析时间
        dns_start = time.time()
        dns_result = resolve_dns(hostname)
        dns_time = (time.time() - dns_start) * 1000  # 转换为毫秒
        
        if not dns_result["success"]:
            return {
                "status": "failed",
                "response_time": (time.time() - start_time) * 1000,
                "message": f"DNS解析失败: {dns_result['error']}",
                "webstatus": "异常",
                "details": {
                    "dns_time": dns_time,
                    "dns_error": dns_result["error"]
                }
            }
        
        # 2. TCP连接时间
        tcp_start = time.time()
        tcp_result = test_tcp_connection(hostname, port, timeout)
        tcp_time = (time.time() - tcp_start) * 1000
        
        if not tcp_result["success"]:
            return {
                "status": "failed",
                "response_time": (time.time() - start_time) * 1000,
                "message": f"TCP连接失败: {tcp_result['error']}",
                "webstatus": "异常",
                "details": {
                    "dns_time": dns_time,
                    "tcp_time": tcp_time,
                    "tcp_error": tcp_result["error"]
                }
            }
        
        # 3. SSL握手时间（仅HTTPS）
        ssl_time = 0
        if is_https:
            ssl_start = time.time()
            ssl_result = test_ssl_handshake(hostname, port, timeout)
            ssl_time = (time.time() - ssl_start) * 1000
            
            if not ssl_result["success"]:
                return {
                    "status": "failed",
                    "response_time": (time.time() - start_time) * 1000,
                    "message": f"SSL握手失败: {ssl_result['error']}",
                    "webstatus": "异常",
                    "details": {
                        "dns_time": dns_time,
                        "tcp_time": tcp_time,
                        "ssl_time": ssl_time,
                        "ssl_error": ssl_result["error"]
                    }
                }
        
        # 4. HTTP请求
        http_start = time.time()
        http_result = send_http_request(target, method, headers, timeout, follow_redirects)
        http_time = (time.time() - http_start) * 1000
        
        total_time = (time.time() - start_time) * 1000
        
        if http_result["success"]:
            response = http_result["response"]
            
            # 计算首字节时间和下载时间
            first_byte_time = http_result.get("first_byte_time", 0)
            download_time = http_result.get("download_time", 0)
            
            return {
                "status": "success",
                "response_time": total_time,
                "message": f"HTTP请求成功，状态码: {response.status_code}",
                "webstatus": "正常",
                "details": {
                    "dns_time": dns_time,
                    "tcp_time": tcp_time,
                    "ssl_time": ssl_time,
                    "first_byte_time": first_byte_time,
                    "download_time": download_time,
                    "http_time": http_time,
                    "status_code": response.status_code,
                    "response_headers": dict(response.headers),
                    "content_length": len(response.content),
                    "dns_ips": dns_result.get("ips", []),
                    "final_url": response.url
                }
            }
        else:
            return {
                "status": "failed",
                "response_time": total_time,
                "message": f"HTTP请求失败: {http_result['error']}",
                "webstatus": "异常",
                "details": {
                    "dns_time": dns_time,
                    "tcp_time": tcp_time,
                    "ssl_time": ssl_time,
                    "http_error": http_result["error"]
                }
            }
            
    except Exception as e:
        total_time = (time.time() - start_time) * 1000 if 'start_time' in locals() else 0
        logger.error(f"HTTP任务 {task_id} 执行异常: {str(e)}")
        return {
            "status": "failed",
            "response_time": total_time,
            "message": f"任务执行异常: {str(e)}",
            "webstatus": "异常",
            "details": {
                "error": str(e)
            }
        }

def resolve_dns(hostname: str) -> Dict[str, Any]:
    """
    解析DNS
    
    Args:
        hostname: 主机名
        
    Returns:
        解析结果
    """
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 5
        resolver.lifetime = 10
        
        answers = resolver.resolve(hostname, 'A')
        ips = [str(answer) for answer in answers]
        
        return {
            "success": True,
            "ips": ips
        }
    except dns.exception.DNSException as e:
        logger.error(f"DNS解析失败 {hostname}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"DNS解析异常 {hostname}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def test_tcp_connection(hostname: str, port: int, timeout: int) -> Dict[str, Any]:
    """
    测试TCP连接
    
    Args:
        hostname: 主机名
        port: 端口
        timeout: 超时时间
        
    Returns:
        连接结果
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        result = sock.connect_ex((hostname, port))
        sock.close()
        
        if result == 0:
            return {"success": True}
        else:
            return {
                "success": False,
                "error": f"连接失败，错误码: {result}"
            }
    except socket.timeout:
        return {
            "success": False,
            "error": "连接超时"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def test_ssl_handshake(hostname: str, port: int, timeout: int) -> Dict[str, Any]:
    """
    测试SSL握手
    
    Args:
        hostname: 主机名
        port: 端口
        timeout: 超时时间
        
    Returns:
        握手结果
    """
    try:
        context = ssl.create_default_context()
        # 在测试环境中跳过证书验证
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with socket.create_connection((hostname, port), timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                # 获取证书信息
                try:
                    cert = ssock.getpeercert()
                    return {
                        "success": True,
                        "cert_subject": cert.get('subject', []) if cert else [],
                        "cert_issuer": cert.get('issuer', []) if cert else [],
                        "cert_version": cert.get('version', 0) if cert else 0
                    }
                except:
                    # 即使无法获取证书信息，SSL握手成功也算成功
                    return {
                        "success": True,
                        "cert_subject": [],
                        "cert_issuer": [],
                        "cert_version": 0
                    }
    except ssl.SSLError as e:
        return {
            "success": False,
            "error": f"SSL错误: {str(e)}"
        }
    except socket.timeout:
        return {
            "success": False,
            "error": "SSL握手超时"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def send_http_request(url: str, method: str, headers: Dict[str, str], timeout: int, follow_redirects: bool) -> Dict[str, Any]:
    """
    发送HTTP请求
    
    Args:
        url: 请求URL
        method: 请求方法
        headers: 请求头
        timeout: 超时时间
        follow_redirects: 是否跟随重定向
        
    Returns:
        请求结果
    """
    try:
        # 设置默认User-Agent
        if 'User-Agent' not in headers:
            headers['User-Agent'] = 'IT-Dialer-Agent/1.0'
        
        # 创建session以便复用连接
        session = requests.Session()
        session.headers.update(headers)
        
        # 跳过SSL证书验证
        session.verify = False
        
        # 记录首字节时间
        first_byte_start = time.time()
        
        response = session.request(
            method=method,
            url=url,
            timeout=timeout,
            allow_redirects=follow_redirects,
            stream=True  # 使用流式下载以计算首字节时间
        )
        
        # 计算首字节时间
        first_byte_time = (time.time() - first_byte_start) * 1000
        
        # 下载内容
        download_start = time.time()
        content = response.content  # 这会触发完整下载
        download_time = (time.time() - download_start) * 1000
        
        return {
            "success": True,
            "response": response,
            "first_byte_time": first_byte_time,
            "download_time": download_time
        }
        
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "请求超时"
        }
    except requests.exceptions.ConnectionError as e:
        return {
            "success": False,
            "error": f"连接错误: {str(e)}"
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"请求异常: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    # 测试代码
    test_task = {
        "task_id": "test_http",
        "type": "http",
        "target": "https://www.baidu.com",
        "params": {
            "method": "GET",
            "timeout": 10
        }
    }
    
    result = execute(test_task)
    print(json.dumps(result, indent=2, ensure_ascii=False))