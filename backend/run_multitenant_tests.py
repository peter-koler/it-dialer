#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多租户功能测试运行脚本
执行所有多租户相关的测试，包括单元测试和集成测试
"""

import os
import sys
import unittest
import subprocess
import time
import requests
import signal
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'app'))

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def print_colored(text, color=Colors.WHITE):
    """打印彩色文本"""
    print(f"{color}{text}{Colors.END}")


def print_header(text):
    """打印标题"""
    print_colored(f"\n{'='*60}", Colors.CYAN)
    print_colored(f"{text:^60}", Colors.CYAN + Colors.BOLD)
    print_colored(f"{'='*60}", Colors.CYAN)


def print_section(text):
    """打印章节标题"""
    print_colored(f"\n{'-'*40}", Colors.BLUE)
    print_colored(f"{text}", Colors.BLUE + Colors.BOLD)
    print_colored(f"{'-'*40}", Colors.BLUE)


def check_service_health(url, timeout=30):
    """检查服务健康状态"""
    print_colored(f"检查服务健康状态: {url}", Colors.YELLOW)
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url}/v1/health", timeout=5)
            if response.status_code == 200:
                print_colored("✓ 服务运行正常", Colors.GREEN)
                return True
        except requests.exceptions.RequestException:
            pass
        
        print_colored("等待服务启动...", Colors.YELLOW)
        time.sleep(2)
    
    print_colored("✗ 服务健康检查失败", Colors.RED)
    return False


def run_unit_tests():
    """运行单元测试"""
    print_section("运行多租户单元测试")
    
    # 设置测试环境变量
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['TESTING'] = 'true'
    
    # 运行单元测试
    test_files = [
        'test_multitenant.py'
    ]
    
    results = {}
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print_colored(f"\n运行测试文件: {test_file}", Colors.CYAN)
            
            try:
                # 使用unittest运行测试
                result = subprocess.run([
                    sys.executable, '-m', 'unittest', test_file.replace('.py', ''), '-v'
                ], capture_output=True, text=True, cwd=project_root)
                
                if result.returncode == 0:
                    print_colored(f"✓ {test_file} 测试通过", Colors.GREEN)
                    results[test_file] = 'PASSED'
                else:
                    print_colored(f"✗ {test_file} 测试失败", Colors.RED)
                    print_colored(f"错误输出:\n{result.stderr}", Colors.RED)
                    results[test_file] = 'FAILED'
                    
                # 打印测试输出
                if result.stdout:
                    print(result.stdout)
                    
            except Exception as e:
                print_colored(f"✗ 运行 {test_file} 时发生异常: {str(e)}", Colors.RED)
                results[test_file] = 'ERROR'
        else:
            print_colored(f"⚠ 测试文件不存在: {test_file}", Colors.YELLOW)
            results[test_file] = 'NOT_FOUND'
    
    return results


def run_integration_tests(backend_url='http://localhost:5000/api'):
    """运行集成测试"""
    print_section("运行多租户集成测试")
    
    # 检查后端服务
    if not check_service_health(backend_url):
        print_colored("后端服务未运行，跳过集成测试", Colors.YELLOW)
        return {'integration_tests': 'SKIPPED'}
    
    # 运行集成测试
    test_files = [
        'test_multitenant_integration.py'
    ]
    
    results = {}
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print_colored(f"\n运行集成测试文件: {test_file}", Colors.CYAN)
            
            try:
                # 设置环境变量
                env = os.environ.copy()
                env['BACKEND_URL'] = backend_url
                env['TESTING'] = 'true'
                
                result = subprocess.run([
                    sys.executable, test_file
                ], capture_output=True, text=True, cwd=project_root, env=env)
                
                if result.returncode == 0:
                    print_colored(f"✓ {test_file} 集成测试通过", Colors.GREEN)
                    results[test_file] = 'PASSED'
                else:
                    print_colored(f"✗ {test_file} 集成测试失败", Colors.RED)
                    print_colored(f"错误输出:\n{result.stderr}", Colors.RED)
                    results[test_file] = 'FAILED'
                    
                # 打印测试输出
                if result.stdout:
                    print(result.stdout)
                    
            except Exception as e:
                print_colored(f"✗ 运行 {test_file} 时发生异常: {str(e)}", Colors.RED)
                results[test_file] = 'ERROR'
        else:
            print_colored(f"⚠ 集成测试文件不存在: {test_file}", Colors.YELLOW)
            results[test_file] = 'NOT_FOUND'
    
    return results


def run_security_tests():
    """运行安全测试"""
    print_section("运行多租户安全测试")
    
    # 这里可以添加专门的安全测试
    # 比如测试SQL注入、权限绕过等
    
    security_checks = [
        "跨租户数据访问防护",
        "权限控制验证",
        "JWT令牌安全性",
        "API端点访问控制",
        "数据库查询过滤"
    ]
    
    print_colored("安全检查项目:", Colors.MAGENTA)
    for check in security_checks:
        print_colored(f"  • {check}", Colors.WHITE)
    
    # 实际的安全测试逻辑应该在这里实现
    print_colored("\n安全测试需要在实际环境中手动验证", Colors.YELLOW)
    
    return {'security_tests': 'MANUAL_VERIFICATION_REQUIRED'}


def run_performance_tests():
    """运行性能测试"""
    print_section("运行多租户性能测试")
    
    performance_metrics = [
        "租户数据查询响应时间",
        "并发用户访问性能",
        "大数据集隔离性能",
        "内存使用情况",
        "数据库查询优化"
    ]
    
    print_colored("性能测试指标:", Colors.MAGENTA)
    for metric in performance_metrics:
        print_colored(f"  • {metric}", Colors.WHITE)
    
    # 实际的性能测试逻辑
    print_colored("\n性能测试需要在生产环境中进行基准测试", Colors.YELLOW)
    
    return {'performance_tests': 'BENCHMARK_REQUIRED'}


def generate_test_report(results):
    """生成测试报告"""
    print_header("多租户功能测试报告")
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    skipped_tests = 0
    
    print_colored(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", Colors.CYAN)
    print_colored(f"测试环境: {os.environ.get('FLASK_ENV', 'development')}", Colors.CYAN)
    
    print_section("测试结果汇总")
    
    for category, category_results in results.items():
        print_colored(f"\n{category.upper()}:", Colors.BOLD)
        
        if isinstance(category_results, dict):
            for test_name, status in category_results.items():
                total_tests += 1
                
                if status == 'PASSED':
                    print_colored(f"  ✓ {test_name}: {status}", Colors.GREEN)
                    passed_tests += 1
                elif status == 'FAILED' or status == 'ERROR':
                    print_colored(f"  ✗ {test_name}: {status}", Colors.RED)
                    failed_tests += 1
                else:
                    print_colored(f"  ⚠ {test_name}: {status}", Colors.YELLOW)
                    skipped_tests += 1
        else:
            total_tests += 1
            if 'PASSED' in str(category_results):
                print_colored(f"  ✓ {category}: {category_results}", Colors.GREEN)
                passed_tests += 1
            elif 'FAILED' in str(category_results) or 'ERROR' in str(category_results):
                print_colored(f"  ✗ {category}: {category_results}", Colors.RED)
                failed_tests += 1
            else:
                print_colored(f"  ⚠ {category}: {category_results}", Colors.YELLOW)
                skipped_tests += 1
    
    print_section("统计信息")
    print_colored(f"总测试数: {total_tests}", Colors.CYAN)
    print_colored(f"通过: {passed_tests}", Colors.GREEN)
    print_colored(f"失败: {failed_tests}", Colors.RED)
    print_colored(f"跳过: {skipped_tests}", Colors.YELLOW)
    
    if total_tests > 0:
        success_rate = (passed_tests / total_tests) * 100
        print_colored(f"成功率: {success_rate:.1f}%", Colors.CYAN)
        
        if success_rate >= 90:
            print_colored("\n🎉 多租户功能测试整体通过！", Colors.GREEN + Colors.BOLD)
        elif success_rate >= 70:
            print_colored("\n⚠️  多租户功能测试部分通过，需要关注失败项", Colors.YELLOW + Colors.BOLD)
        else:
            print_colored("\n❌ 多租户功能测试存在严重问题，需要立即修复", Colors.RED + Colors.BOLD)
    
    return {
        'total': total_tests,
        'passed': passed_tests,
        'failed': failed_tests,
        'skipped': skipped_tests,
        'success_rate': success_rate if total_tests > 0 else 0
    }


def main():
    """主函数"""
    print_header("多租户功能测试套件")
    
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='运行多租户功能测试')
    parser.add_argument('--unit-only', action='store_true', help='只运行单元测试')
    parser.add_argument('--integration-only', action='store_true', help='只运行集成测试')
    parser.add_argument('--backend-url', default='http://localhost:5000/api', help='后端服务URL')
    parser.add_argument('--skip-service-check', action='store_true', help='跳过服务健康检查')
    
    args = parser.parse_args()
    
    results = {}
    
    try:
        # 运行单元测试
        if not args.integration_only:
            results['unit_tests'] = run_unit_tests()
        
        # 运行集成测试
        if not args.unit_only:
            results['integration_tests'] = run_integration_tests(args.backend_url)
        
        # 运行安全测试
        if not args.unit_only and not args.integration_only:
            results['security_tests'] = run_security_tests()
            results['performance_tests'] = run_performance_tests()
        
        # 生成测试报告
        summary = generate_test_report(results)
        
        # 根据测试结果设置退出码
        if summary['failed'] > 0:
            sys.exit(1)
        elif summary['total'] == 0:
            print_colored("\n⚠️  没有运行任何测试", Colors.YELLOW)
            sys.exit(2)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print_colored("\n\n测试被用户中断", Colors.YELLOW)
        sys.exit(130)
    except Exception as e:
        print_colored(f"\n\n测试运行过程中发生异常: {str(e)}", Colors.RED)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()