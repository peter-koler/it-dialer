from app import create_app, db
from app.models.system_variable import SystemVariable

def init_system_variables_table():
    app = create_app()
    with app.app_context():
        # 检查表是否存在，如果不存在则创建
        if not hasattr(SystemVariable, '__table__'):
            print("SystemVariable model not properly defined")
            return
            
        # 检查表是否已存在
        inspector = db.inspect(db.engine)
        if 'system_variables' not in inspector.get_table_names():
            # 创建表
            db.create_all()
            print("Created system_variables table")
        else:
            print("system_variables table already exists")

if __name__ == '__main__':
    init_system_variables_table()