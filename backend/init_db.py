import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, Task, Result, Node

def init_db():
    app = create_app()
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("数据库表创建成功")

if __name__ == '__main__':
    init_db()