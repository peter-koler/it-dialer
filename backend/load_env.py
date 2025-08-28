#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境变量加载器
从配置文件中加载环境变量
"""

import os


def load_env_from_file(file_path='logging.conf'):
    """从配置文件加载环境变量
    
    Args:
        file_path: 配置文件路径
    """
    if not os.path.exists(file_path):
        print(f"配置文件 {file_path} 不存在，使用默认配置")
        return
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过空行和注释行
                if not line or line.startswith('#'):
                    continue
                
                # 解析键值对
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 只有当环境变量未设置时才设置
                    if key and not os.environ.get(key):
                        os.environ[key] = value
                        print(f"从配置文件加载环境变量: {key}={value}")
        
        print(f"成功从 {file_path} 加载配置")
    except Exception as e:
        print(f"加载配置文件 {file_path} 时出错: {e}")


if __name__ == '__main__':
    # 测试加载配置
    load_env_from_file()
    print("当前环境变量:")
    for key in ['LOG_FILE', 'LOG_LEVEL', 'LOG_MAX_BYTES', 'LOG_BACKUP_COUNT']:
        print(f"  {key}: {os.environ.get(key, '未设置')}")