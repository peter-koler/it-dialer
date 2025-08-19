import sqlite3
import os
from datetime import datetime

# 连接到数据库
db_path = os.path.join(os.path.dirname(__file__), 'app.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # 查看当前的外键约束
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='results'")
    table_info = cursor.fetchone()
    print("Current results table definition:")
    print(table_info[0])
    
    # 删除可能存在的新表
    cursor.execute('DROP TABLE IF EXISTS results_new')
    
    # 由于SQLite限制，需要重新创建表来添加CASCADE约束
    # 1. 创建新表
    cursor.execute('''
        CREATE TABLE results_new (
            id INTEGER PRIMARY KEY,
            task_id INTEGER NOT NULL,
            status VARCHAR(50) NOT NULL,
            response_time FLOAT,
            message TEXT,
            details TEXT,
            agent_id VARCHAR(100),
            agent_area VARCHAR(100),
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(task_id) REFERENCES tasks (id) ON DELETE CASCADE
        )
    ''')
    
    # 2. 复制数据
    cursor.execute('''
        INSERT INTO results_new (id, task_id, status, response_time, message, details, agent_id, agent_area, created_at)
        SELECT id, task_id, status, response_time, message, details, agent_id, agent_area, 
               CASE 
                   WHEN created_at IS NULL THEN datetime('now')
                   ELSE created_at
               END
        FROM results
    ''')
    
    # 3. 删除旧表
    cursor.execute('DROP TABLE results')
    
    # 4. 重命名新表
    cursor.execute('ALTER TABLE results_new RENAME TO results')
    
    # 5. 重新创建索引（如果有的话）
    # 这里根据需要添加索引
    
    conn.commit()
    print("Foreign key constraint updated successfully!")
    
except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
finally:
    conn.close()