# -*- coding: utf-8 -*-
"""
邮件服务工具类
提供邮件发送功能，支持报表推送
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import List, Optional, Dict, Any
import io

from app.utils.export_utils import ExportUtils

logger = logging.getLogger(__name__)


class EmailService:
    """邮件服务类"""
    
    def __init__(self, smtp_server: str = None, smtp_port: int = None, 
                 username: str = None, password: str = None, use_tls: bool = True):
        """初始化邮件服务
        
        Args:
            smtp_server: SMTP服务器地址
            smtp_port: SMTP端口
            username: 邮箱用户名
            password: 邮箱密码或授权码
            use_tls: 是否使用TLS加密
        """
        # 默认配置（可以从环境变量或配置文件读取）
        self.smtp_server = smtp_server or 'smtp.qq.com'
        self.smtp_port = smtp_port or 587
        self.username = username or ''
        self.password = password or ''
        self.use_tls = use_tls
        
    def send_email(self, to_emails: List[str], subject: str, body: str, 
                   attachments: List[Dict[str, Any]] = None, is_html: bool = False) -> bool:
        """发送邮件
        
        Args:
            to_emails: 收件人邮箱列表
            subject: 邮件主题
            body: 邮件正文
            attachments: 附件列表，格式: [{'filename': 'xxx', 'content': bytes, 'mimetype': 'xxx'}]
            is_html: 是否为HTML格式
            
        Returns:
            bool: 发送是否成功
        """
        try:
            # 创建邮件对象
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            # 添加邮件正文
            if is_html:
                msg.attach(MIMEText(body, 'html', 'utf-8'))
            else:
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # 添加附件
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['content'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment["filename"]}'
                    )
                    msg.attach(part)
            
            # 连接SMTP服务器并发送邮件
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            
            if self.use_tls:
                server.starttls()
                
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"邮件发送成功: {subject} -> {', '.join(to_emails)}")
            return True
            
        except Exception as e:
            logger.error(f"邮件发送失败: {str(e)}")
            return False
    
    def send_report_email(self, to_emails: List[str], report_name: str, 
                         report_data: List[Dict[str, Any]], export_format: str = 'excel',
                         additional_info: str = '') -> bool:
        """发送报表邮件
        
        Args:
            to_emails: 收件人邮箱列表
            report_name: 报表名称
            report_data: 报表数据
            export_format: 导出格式 ('excel' 或 'pdf')
            additional_info: 额外信息
            
        Returns:
            bool: 发送是否成功
        """
        try:
            # 生成报表文件
            if export_format.lower() == 'excel':
                file_stream = ExportUtils.export_to_excel(report_data)
                filename = ExportUtils.get_export_filename('excel', report_name)
                mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            else:  # pdf
                file_stream = ExportUtils.export_to_pdf(report_data, title=report_name)
                filename = ExportUtils.get_export_filename('pdf', report_name)
                mimetype = 'application/pdf'
            
            # 准备附件
            attachments = [{
                'filename': filename,
                'content': file_stream.getvalue(),
                'mimetype': mimetype
            }]
            
            # 生成邮件内容
            subject = f"定时报表推送 - {report_name}"
            body = self._generate_report_email_body(report_name, report_data, additional_info)
            
            # 发送邮件
            return self.send_email(
                to_emails=to_emails,
                subject=subject,
                body=body,
                attachments=attachments,
                is_html=True
            )
            
        except Exception as e:
            logger.error(f"发送报表邮件失败: {str(e)}")
            return False
    
    def _generate_report_email_body(self, report_name: str, report_data: List[Dict[str, Any]], 
                                   additional_info: str = '') -> str:
        """生成报表邮件正文
        
        Args:
            report_name: 报表名称
            report_data: 报表数据
            additional_info: 额外信息
            
        Returns:
            str: HTML格式的邮件正文
        """
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data_count = len(report_data)
        
        # 生成数据预览（最多显示5条）
        preview_data = report_data[:5] if report_data else []
        preview_html = ''
        
        if preview_data:
            # 获取列名
            columns = list(preview_data[0].keys()) if preview_data else []
            
            preview_html = '<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%; margin: 10px 0;">'
            
            # 表头
            preview_html += '<thead><tr style="background-color: #f0f0f0;">'
            for column in columns:
                preview_html += f'<th style="padding: 8px; text-align: left;">{column}</th>'
            preview_html += '</tr></thead>'
            
            # 数据行
            preview_html += '<tbody>'
            for row in preview_data:
                preview_html += '<tr>'
                for column in columns:
                    value = row.get(column, '')
                    if isinstance(value, (list, dict)):
                        value = str(value)[:50] + '...' if len(str(value)) > 50 else str(value)
                    preview_html += f'<td style="padding: 8px;">{value}</td>'
                preview_html += '</tr>'
            preview_html += '</tbody></table>'
            
            if data_count > 5:
                preview_html += f'<p style="color: #666; font-style: italic;">... 还有 {data_count - 5} 条数据，请查看附件获取完整报表</p>'
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>报表推送</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                    📊 定时报表推送
                </h2>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #495057;">报表信息</h3>
                    <p><strong>报表名称:</strong> {report_name}</p>
                    <p><strong>生成时间:</strong> {current_time}</p>
                    <p><strong>数据条数:</strong> {data_count} 条</p>
                </div>
                
                {f'<div style="margin: 20px 0;"><h3 style="color: #495057;">数据预览</h3>{preview_html}</div>' if preview_html else ''}
                
                {f'<div style="background-color: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0;"><h3 style="margin-top: 0; color: #0c5460;">附加信息</h3><p>{additional_info}</p></div>' if additional_info else ''}
                
                <div style="background-color: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #155724;">📎 附件说明</h3>
                    <p>完整的报表数据已作为附件发送，请下载查看详细内容。</p>
                </div>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; color: #6c757d; font-size: 12px;">
                    <p>此邮件由系统自动发送，请勿直接回复。</p>
                    <p>如有疑问，请联系系统管理员。</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_body
    
    def test_connection(self) -> bool:
        """测试邮件服务器连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            
            if self.use_tls:
                server.starttls()
                
            server.login(self.username, self.password)
            server.quit()
            
            logger.info("邮件服务器连接测试成功")
            return True
            
        except Exception as e:
            logger.error(f"邮件服务器连接测试失败: {str(e)}")
            return False
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'EmailService':
        """从配置创建邮件服务实例
        
        Args:
            config: 邮件配置字典
            
        Returns:
            EmailService: 邮件服务实例
        """
        return cls(
            smtp_server=config.get('SMTP_SERVER'),
            smtp_port=config.get('SMTP_PORT', 587),
            username=config.get('SMTP_USERNAME'),
            password=config.get('SMTP_PASSWORD'),
            use_tls=config.get('SMTP_USE_TLS', True)
        )


# 全局邮件服务实例
_email_service = None


def get_email_service() -> EmailService:
    """获取全局邮件服务实例"""
    global _email_service
    if _email_service is None:
        # 这里可以从配置文件或环境变量读取配置
        _email_service = EmailService()
    return _email_service


def init_email_service(config: Dict[str, Any]) -> None:
    """初始化全局邮件服务"""
    global _email_service
    _email_service = EmailService.from_config(config)