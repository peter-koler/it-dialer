import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# 加载环境变量配置
from load_env import load_env_from_file
load_env_from_file('logging.conf')

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)