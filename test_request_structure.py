#!/usr/bin/env python3
import sys
import os
sys.path.append('/Users/peter/Documents/code/boce/it-dialer/agent')

import json
from plugins.api import execute_step

# 测试单个步骤
step_config = {
    'step_id': '1',
    'name': 'Test Step',
    'request': {
        'method': 'GET',
        'url': 'http://localhost:6000/ip',
        'headers': [{'key': 'Content-Type', 'value': 'application/json'}],
        'body': {
            'type': 'json',
            'content': '{"test": "value"}'
        }
    }
}

print('Testing API step request structure...')
try:
    # 直接测试步骤执行
    context = {}
    step_result = execute_step(step_config, context)
    
    print('\nStep execution status:', step_result.get('status'))
    print('Step data keys:', list(step_result.keys()))
    
    request_data = step_result.get('request', {})
    print('\nRequest data structure:')
    print(json.dumps(request_data, indent=2))
    
    response_data = step_result.get('response', {})
    print('\nResponse data keys:', list(response_data.keys()))
    if response_data:
        print('Response status code:', response_data.get('status_code'))
        
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()