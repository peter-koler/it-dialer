import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'dev-jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)
    
    # Environment
    ENV = os.environ.get('ENV') or 'development'
    
    # Database configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, '..', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Scheduler
    SCHEDULER_API_ENABLED = True
    
    # Logging configuration
    LOG_FILE = os.environ.get('LOG_FILE') or os.path.join(basedir, '..', 'logs', 'backend.log')
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', 10 * 1024 * 1024))  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 5))  # 保留5个备份文件
    
    # Agent Token
    AGENT_TOKEN = os.environ.get('AGENT_TOKEN') or 'agent-default-token-2024'
    
    # CORS
    ALLOWED_ORIGINS = [
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:8081",
        "http://127.0.0.1:8081"
    ]