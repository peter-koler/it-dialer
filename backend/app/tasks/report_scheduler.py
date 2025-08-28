# -*- coding: utf-8 -*-
"""
报表定时推送任务
处理报表订阅的定时推送功能
"""

import logging
from datetime import datetime, timedelta
from typing import List

from app.models.report import Report, ReportSubscription
from app.models.task import Task
from app.models.result import Result
from app.utils.email_service import get_email_service
from app.api.reports import ReportGenerateAPI
from app import db

logger = logging.getLogger(__name__)


class ReportScheduler:
    """报表定时推送调度器"""
    
    @staticmethod
    def send_daily_reports():
        """发送每日报表"""
        logger.info("开始执行每日报表推送任务")
        ReportScheduler._send_reports_by_frequency('daily')
    
    @staticmethod
    def send_weekly_reports():
        """发送每周报表"""
        logger.info("开始执行每周报表推送任务")
        ReportScheduler._send_reports_by_frequency('weekly')
    
    @staticmethod
    def send_monthly_reports():
        """发送每月报表"""
        logger.info("开始执行每月报表推送任务")
        ReportScheduler._send_reports_by_frequency('monthly')
    
    @staticmethod
    def _send_reports_by_frequency(frequency: str):
        """根据频率发送报表
        
        Args:
            frequency: 推送频率 ('daily', 'weekly', 'monthly')
        """
        try:
            # 获取指定频率的活跃订阅
            subscriptions = ReportSubscription.query.filter_by(
                frequency=frequency,
                is_active=True
            ).all()
            
            if not subscriptions:
                logger.info(f"没有找到 {frequency} 频率的活跃订阅")
                return
            
            logger.info(f"找到 {len(subscriptions)} 个 {frequency} 频率的订阅")
            
            # 按报表分组处理订阅
            report_subscriptions = {}
            for subscription in subscriptions:
                report_id = subscription.report_id
                if report_id not in report_subscriptions:
                    report_subscriptions[report_id] = []
                report_subscriptions[report_id].append(subscription)
            
            # 处理每个报表的订阅
            for report_id, subs in report_subscriptions.items():
                try:
                    ReportScheduler._process_report_subscriptions(report_id, subs, frequency)
                except Exception as e:
                    logger.error(f"处理报表 {report_id} 的订阅时出错: {str(e)}")
                    continue
            
            logger.info(f"{frequency} 报表推送任务完成")
            
        except Exception as e:
            logger.error(f"执行 {frequency} 报表推送任务失败: {str(e)}")
    
    @staticmethod
    def _process_report_subscriptions(report_id: int, subscriptions: List[ReportSubscription], frequency: str):
        """处理单个报表的订阅推送
        
        Args:
            report_id: 报表ID
            subscriptions: 订阅列表
            frequency: 推送频率
        """
        try:
            # 获取报表信息
            report = Report.query.get(report_id)
            if not report:
                logger.warning(f"报表 {report_id} 不存在，跳过推送")
                return
            
            logger.info(f"开始处理报表 '{report.name}' 的 {len(subscriptions)} 个订阅")
            
            # 计算日期范围
            end_date = datetime.now()
            if frequency == 'daily':
                start_date = end_date - timedelta(days=1)
            elif frequency == 'weekly':
                start_date = end_date - timedelta(weeks=1)
            elif frequency == 'monthly':
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=1)
            
            # 生成报表数据
            try:
                generate_api = ReportGenerateAPI()
                report_data = generate_api._generate_report_data(
                    report, start_date, end_date, {}
                )
                
                if not report_data:
                    logger.warning(f"报表 '{report.name}' 没有数据，跳过推送")
                    return
                
                logger.info(f"报表 '{report.name}' 生成了 {len(report_data)} 条数据")
                
            except Exception as e:
                logger.error(f"生成报表 '{report.name}' 数据失败: {str(e)}")
                return
            
            # 获取邮件服务
            email_service = get_email_service()
            
            # 按邮箱分组发送
            email_groups = {}
            for subscription in subscriptions:
                email = subscription.email
                if email not in email_groups:
                    email_groups[email] = []
                email_groups[email].append(subscription)
            
            # 发送邮件
            success_count = 0
            for email, subs in email_groups.items():
                try:
                    # 生成额外信息
                    additional_info = ReportScheduler._generate_additional_info(
                        frequency, start_date, end_date, subs
                    )
                    
                    # 发送报表邮件
                    success = email_service.send_report_email(
                        to_emails=[email],
                        report_name=report.name,
                        report_data=report_data,
                        export_format='excel',  # 默认使用Excel格式
                        additional_info=additional_info
                    )
                    
                    if success:
                        success_count += 1
                        logger.info(f"成功发送报表 '{report.name}' 到 {email}")
                    else:
                        logger.error(f"发送报表 '{report.name}' 到 {email} 失败")
                        
                except Exception as e:
                    logger.error(f"发送邮件到 {email} 时出错: {str(e)}")
                    continue
            
            logger.info(f"报表 '{report.name}' 推送完成，成功发送 {success_count}/{len(email_groups)} 封邮件")
            
        except Exception as e:
            logger.error(f"处理报表 {report_id} 订阅时出错: {str(e)}")
    
    @staticmethod
    def _generate_additional_info(frequency: str, start_date: datetime, 
                                end_date: datetime, subscriptions: List[ReportSubscription]) -> str:
        """生成邮件附加信息
        
        Args:
            frequency: 推送频率
            start_date: 开始日期
            end_date: 结束日期
            subscriptions: 订阅列表
            
        Returns:
            str: 附加信息
        """
        frequency_map = {
            'daily': '每日',
            'weekly': '每周',
            'monthly': '每月'
        }
        
        frequency_text = frequency_map.get(frequency, frequency)
        date_range = f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}"
        
        info = f"""
        <p><strong>推送类型:</strong> {frequency_text}定时推送</p>
        <p><strong>数据时间范围:</strong> {date_range}</p>
        <p><strong>订阅数量:</strong> {len(subscriptions)} 个</p>
        """
        
        return info
    
    @staticmethod
    def send_test_report(subscription_id: int) -> bool:
        """发送测试报表
        
        Args:
            subscription_id: 订阅ID
            
        Returns:
            bool: 发送是否成功
        """
        try:
            # 获取订阅信息
            subscription = ReportSubscription.query.get(subscription_id)
            if not subscription:
                logger.error(f"订阅 {subscription_id} 不存在")
                return False
            
            # 获取报表信息
            report = subscription.report
            if not report:
                logger.error(f"订阅 {subscription_id} 关联的报表不存在")
                return False
            
            logger.info(f"开始发送测试报表: {report.name} -> {subscription.email}")
            
            # 生成测试数据（最近7天）
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            generate_api = ReportGenerateAPI()
            report_data = generate_api._generate_report_data(
                report, start_date, end_date, {}
            )
            
            if not report_data:
                # 如果没有数据，创建示例数据
                report_data = [{
                    '项目': '测试数据',
                    '状态': '正常',
                    '时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    '备注': '这是测试报表数据'
                }]
            
            # 发送邮件
            email_service = get_email_service()
            additional_info = """
            <p><strong>这是一封测试邮件</strong></p>
            <p>用于验证报表推送功能是否正常工作。</p>
            <p>如果您收到此邮件，说明推送功能配置正确。</p>
            """
            
            success = email_service.send_report_email(
                to_emails=[subscription.email],
                report_name=f"[测试] {report.name}",
                report_data=report_data,
                export_format='excel',
                additional_info=additional_info
            )
            
            if success:
                logger.info(f"测试报表发送成功: {report.name} -> {subscription.email}")
            else:
                logger.error(f"测试报表发送失败: {report.name} -> {subscription.email}")
            
            return success
            
        except Exception as e:
            logger.error(f"发送测试报表失败: {str(e)}")
            return False
    
    @staticmethod
    def get_subscription_stats() -> dict:
        """获取订阅统计信息
        
        Returns:
            dict: 统计信息
        """
        try:
            total_subscriptions = ReportSubscription.query.count()
            active_subscriptions = ReportSubscription.query.filter_by(is_active=True).count()
            
            daily_subs = ReportSubscription.query.filter_by(
                frequency='daily', is_active=True
            ).count()
            
            weekly_subs = ReportSubscription.query.filter_by(
                frequency='weekly', is_active=True
            ).count()
            
            monthly_subs = ReportSubscription.query.filter_by(
                frequency='monthly', is_active=True
            ).count()
            
            return {
                'total_subscriptions': total_subscriptions,
                'active_subscriptions': active_subscriptions,
                'inactive_subscriptions': total_subscriptions - active_subscriptions,
                'daily_subscriptions': daily_subs,
                'weekly_subscriptions': weekly_subs,
                'monthly_subscriptions': monthly_subs
            }
            
        except Exception as e:
            logger.error(f"获取订阅统计信息失败: {str(e)}")
            return {}