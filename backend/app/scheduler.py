from apscheduler.schedulers.background import BackgroundScheduler
from app.models.node import Node
from datetime import datetime, timedelta
from app import db
import logging

logger = logging.getLogger(__name__)

def check_node_status(app):
    """检查节点状态，将超时未发送心跳的节点标记为离线"""
    try:
        with app.app_context():
            # 获取所有在线节点
            online_nodes = Node.query.filter_by(status='online').all()
            
            # 计算超时时间（5分钟）
            timeout_threshold = datetime.utcnow() - timedelta(minutes=5)
            
            # 检查每个在线节点的心跳时间
            for node in online_nodes:
                if node.last_heartbeat and node.last_heartbeat < timeout_threshold:
                    # 节点超时，标记为离线
                    node.status = 'offline'
                    logger.info(f"节点 {node.agent_id} 已标记为离线")
            
            # 提交更改
            db.session.commit()
            
    except Exception as e:
        logger.error(f"检查节点状态时发生错误: {e}")

def start_scheduler(app):
    """启动定时任务调度器"""
    scheduler = BackgroundScheduler()
    
    # 添加检查节点状态的任务，每5分钟执行一次
    scheduler.add_job(
        func=lambda: check_node_status(app),
        trigger="interval",
        minutes=5,
        id='check_node_status'
    )
    
    scheduler.start()
    logger.info("定时任务调度器已启动")
    
    return scheduler