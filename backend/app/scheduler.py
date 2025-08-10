from apscheduler.schedulers.background import BackgroundScheduler
import logging

logger = logging.getLogger(__name__)

def start_scheduler(app):
    """启动定时任务调度器"""
    scheduler = BackgroundScheduler()
    
    # 添加检查节点状态的任务，每5分钟执行一次
    from app.api.v1.nodes import check_node_status
    scheduler.add_job(
        func=lambda: check_node_status(app),
        trigger="interval",
        minutes=5,
        id='check_node_status'
    )
    
    scheduler.start()
    logger.info("定时任务调度器已启动")
    
    return scheduler