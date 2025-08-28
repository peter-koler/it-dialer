#!/usr/bin/env python3
"""
移除Node表中的tenant_id字段，使节点成为全局共享资源

这个脚本将：
1. 移除nodes表中的tenant_id字段
2. 移除相关的外键约束
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from sqlalchemy import text

def remove_node_tenant_binding():
    """移除节点的租户绑定"""
    app = create_app()
    
    with app.app_context():
        try:
            print("开始移除Node表的租户绑定...")
            
            # 检查数据库类型
            engine = db.engine
            dialect = engine.dialect.name
            
            if dialect == 'sqlite':
                # SQLite不支持直接删除列，需要重建表
                print("检测到SQLite数据库，将重建nodes表...")
                
                # 创建新的nodes表结构（不包含tenant_id）
                db.session.execute(text("""
                    CREATE TABLE nodes_new (
                        id INTEGER PRIMARY KEY,
                        agent_id VARCHAR(100) UNIQUE NOT NULL,
                        agent_area VARCHAR(100) NOT NULL,
                        ip_address VARCHAR(50) NOT NULL,
                        hostname VARCHAR(100) NOT NULL,
                        status VARCHAR(20) DEFAULT 'offline',
                        last_heartbeat DATETIME,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # 复制数据（排除tenant_id字段）
                db.session.execute(text("""
                    INSERT INTO nodes_new (
                        id, agent_id, agent_area, ip_address, hostname, 
                        status, last_heartbeat, created_at, updated_at
                    )
                    SELECT 
                        id, agent_id, agent_area, ip_address, hostname,
                        status, last_heartbeat, created_at, updated_at
                    FROM nodes
                """))
                
                # 删除旧表
                db.session.execute(text("DROP TABLE nodes"))
                
                # 重命名新表
                db.session.execute(text("ALTER TABLE nodes_new RENAME TO nodes"))
                
            elif dialect == 'mysql':
                print("检测到MySQL数据库，删除tenant_id字段...")
                
                # 删除外键约束（如果存在）
                try:
                    db.session.execute(text("ALTER TABLE nodes DROP FOREIGN KEY nodes_ibfk_1"))
                except Exception as e:
                    print(f"删除外键约束时出现错误（可能不存在）: {e}")
                
                # 删除tenant_id字段
                db.session.execute(text("ALTER TABLE nodes DROP COLUMN tenant_id"))
                
            elif dialect == 'postgresql':
                print("检测到PostgreSQL数据库，删除tenant_id字段...")
                
                # 删除外键约束（如果存在）
                try:
                    db.session.execute(text("ALTER TABLE nodes DROP CONSTRAINT IF EXISTS nodes_tenant_id_fkey"))
                except Exception as e:
                    print(f"删除外键约束时出现错误: {e}")
                
                # 删除tenant_id字段
                db.session.execute(text("ALTER TABLE nodes DROP COLUMN IF EXISTS tenant_id"))
            
            # 提交更改
            db.session.commit()
            print("✅ 成功移除Node表的租户绑定")
            
            # 验证更改
            result = db.session.execute(text("SELECT COUNT(*) as count FROM nodes"))
            count = result.fetchone()[0]
            print(f"✅ 验证完成，当前节点数量: {count}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 移除租户绑定失败: {str(e)}")
            raise

if __name__ == '__main__':
    remove_node_tenant_binding()