import sys
import os
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 设置日志配置
    from logging_config import LoggingConfig
    logging_config = LoggingConfig.from_config(Config)
    logging_config.setup_logging()
    
    # 设置CORS - 开发环境下允许所有来源
    if app.config.get('ENV') == 'development':
        CORS(app, resources={
            r"/api/*": {
                "origins": "*",
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization", "X-Tenant-ID", "x-tenant-id"]
            }
        })
    else:
        # 生产环境使用配置的来源
        CORS(app, resources={
            r"/api/*": {
                "origins": Config.ALLOWED_ORIGINS,
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization", "X-Tenant-ID", "x-tenant-id"]
            }
        })
    
    # 初始化数据库
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    # 注册蓝图
    from app.api.v1 import bp as api_v1_bp
    app.register_blueprint(api_v1_bp, url_prefix='/api/v1')
    
    # 注册v2 API蓝图
    from app.api.v2 import v2_bp
    app.register_blueprint(v2_bp)
    
    # 注册报表蓝图
    from app.api.reports import reports_bp
    app.register_blueprint(reports_bp, url_prefix='/api')
    
    # 注册订阅蓝图
    from app.api.subscriptions import subscriptions_bp
    app.register_blueprint(subscriptions_bp, url_prefix='/api')
    
    # 启动定时任务调度器
    from .scheduler import start_scheduler
    scheduler = start_scheduler(app)
    app.scheduler = scheduler
    
    return app