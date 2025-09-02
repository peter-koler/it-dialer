#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强告警功能简化测试
测试增强告警的核心逻辑，不依赖Flask应用上下文
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

class MockAlertConfig:
    """模拟告警配置类"""
    def __init__(self, config):
        self._config = config
    
    def get_config(self):
        return self._config

class SimpleAlertStateManager:
    """简化的告警状态管理器，用于测试"""
    
    def __init__(self):
        self.cache = {}
    
    def get_agent_state(self, task_id, agent_id, alert_type):
        """获取监测点状态"""
        key = f"{task_id}_{agent_id}_{alert_type}"
        return self.cache.get(key, {
            'consecutive_failures': 0,
            'last_failure_time': None,
            'is_abnormal': False
        })
    
    def update_agent_state(self, task_id, agent_id, alert_type, is_abnormal):
        """更新监测点状态"""
        key = f"{task_id}_{agent_id}_{alert_type}"
        state = self.get_agent_state(task_id, agent_id, alert_type)
        
        if is_abnormal:
            state['consecutive_failures'] += 1
            state['is_abnormal'] = True
        else:
            state['consecutive_failures'] = 0
            state['is_abnormal'] = False
        
        self.cache[key] = state
        return state
    
    def get_abnormal_agents_count(self, task_id, alert_type, alert_config):
        """获取异常监测点数量"""
        config = alert_config.get_config()
        min_occurrences = config.get('min_occurrences', 1)
        
        count = 0
        for key, state in self.cache.items():
            if key.startswith(f"{task_id}_") and key.endswith(f"_{alert_type}"):
                if state['consecutive_failures'] >= min_occurrences:
                    count += 1
        return count
    
    def check_trigger_conditions(self, task_id, agent_id, alert_type, alert_config):
        """检查告警触发条件"""
        config = alert_config.get_config()
        min_points = config.get('min_points', 1)
        min_occurrences = config.get('min_occurrences', 1)
        trigger_mode = config.get('trigger_mode', 'OR')
        
        # 获取当前监测点状态
        agent_state = self.get_agent_state(task_id, agent_id, alert_type)
        consecutive_count = agent_state['consecutive_failures']
        
        # 获取异常监测点总数
        abnormal_points_count = self.get_abnormal_agents_count(task_id, alert_type, alert_config)
        
        # 检查触发条件
        consecutive_triggered = consecutive_count >= min_occurrences
        points_triggered = abnormal_points_count >= min_points
        
        result = {
            'should_trigger': False,
            'trigger_type': None,
            'consecutive_count': consecutive_count,
            'abnormal_points_count': abnormal_points_count,
            'min_points': min_points,
            'min_occurrences': min_occurrences,
            'trigger_mode': trigger_mode
        }
        
        # 根据逻辑模式判断是否触发
        if trigger_mode == 'OR':
            if consecutive_triggered or points_triggered:
                result['should_trigger'] = True
                if consecutive_triggered and points_triggered:
                    result['trigger_type'] = 'both'
                elif consecutive_triggered:
                    result['trigger_type'] = 'consecutive'
                else:
                    result['trigger_type'] = 'point_count'
        elif trigger_mode == 'AND':
            if consecutive_triggered and points_triggered:
                result['should_trigger'] = True
                result['trigger_type'] = 'both'
        
        return result

class TestEnhancedAlert(unittest.TestCase):
    """增强告警功能测试"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.state_manager = SimpleAlertStateManager()
        
        # 创建默认告警配置
        self.alert_config = MockAlertConfig({
            'min_points': 2,
            'min_occurrences': 3,
            'trigger_mode': 'AND'
        })
    
    def test_consecutive_count_tracking(self):
        """测试连续次数统计"""
        task_id = 100
        agent_id = 'agent1'
        alert_type = 'status'
        
        # 第一次异常
        state = self.state_manager.update_agent_state(task_id, agent_id, alert_type, True)
        self.assertEqual(state['consecutive_failures'], 1)
        
        # 第二次异常
        state = self.state_manager.update_agent_state(task_id, agent_id, alert_type, True)
        self.assertEqual(state['consecutive_failures'], 2)
        
        # 恢复正常，计数重置
        state = self.state_manager.update_agent_state(task_id, agent_id, alert_type, False)
        self.assertEqual(state['consecutive_failures'], 0)
    
    def test_multiple_points_abnormal_count(self):
        """测试多个监测点的异常数量统计"""
        task_id = 100
        alert_type = 'status'
        
        # 配置：连续3次异常才算异常监测点
        config = MockAlertConfig({
            'min_points': 2,
            'min_occurrences': 3,
            'trigger_mode': 'AND'
        })
        
        # agent1连续3次异常
        for _ in range(3):
            self.state_manager.update_agent_state(task_id, 'agent1', alert_type, True)
        
        # agent2连续3次异常
        for _ in range(3):
            self.state_manager.update_agent_state(task_id, 'agent2', alert_type, True)
        
        # agent3只有2次异常（不足3次）
        for _ in range(2):
            self.state_manager.update_agent_state(task_id, 'agent3', alert_type, True)
        
        abnormal_count = self.state_manager.get_abnormal_agents_count(task_id, alert_type, config)
        self.assertEqual(abnormal_count, 2)  # 只有agent1和agent2满足条件
    
    def test_and_trigger_mode(self):
        """测试AND逻辑模式：需要同时满足监测点数量和连续次数阈值"""
        task_id = 200
        alert_type = 'status'
        
        # 配置：至少2个监测点异常，且连续3次异常，AND模式
        config = MockAlertConfig({
            'min_points': 2,
            'min_occurrences': 3,
            'trigger_mode': 'AND'
        })
        
        # 只有1个监测点连续3次异常 - 不应触发
        for _ in range(3):
            self.state_manager.update_agent_state(task_id, 'agent1', alert_type, True)
        
        result = self.state_manager.check_trigger_conditions(task_id, 'agent1', alert_type, config)
        self.assertFalse(result['should_trigger'])
        
        # 2个监测点，但只连续2次异常 - 不应触发
        for _ in range(2):
            self.state_manager.update_agent_state(task_id, 'agent2', alert_type, True)
        
        result = self.state_manager.check_trigger_conditions(task_id, 'agent2', alert_type, config)
        self.assertFalse(result['should_trigger'])
        
        # 2个监测点，且都连续3次异常 - 应该触发
        self.state_manager.update_agent_state(task_id, 'agent2', alert_type, True)
        
        result = self.state_manager.check_trigger_conditions(task_id, 'agent2', alert_type, config)
        self.assertTrue(result['should_trigger'])
        self.assertEqual(result['trigger_type'], 'both')
    
    def test_or_trigger_mode(self):
        """测试OR逻辑模式：满足监测点数量或连续次数阈值任一条件即可"""
        task_id = 300
        alert_type = 'status'
        
        # 配置：至少3个监测点异常，或连续2次异常，OR模式
        config = MockAlertConfig({
            'min_points': 3,
            'min_occurrences': 2,
            'trigger_mode': 'OR'
        })
        
        # 只有1个监测点连续2次异常 - 应该触发（满足连续次数条件）
        for _ in range(2):
            self.state_manager.update_agent_state(task_id, 'agent1', alert_type, True)
        
        result = self.state_manager.check_trigger_conditions(task_id, 'agent1', alert_type, config)
        self.assertTrue(result['should_trigger'])
        self.assertEqual(result['trigger_type'], 'consecutive')
        
        # 清理状态，重新测试
        self.state_manager.cache.clear()
        
        # 3个监测点异常，但只连续1次 - 不应触发（因为需要连续2次才算异常监测点）
        self.state_manager.update_agent_state(task_id, 'agent1', alert_type, True)
        self.state_manager.update_agent_state(task_id, 'agent2', alert_type, True)
        self.state_manager.update_agent_state(task_id, 'agent3', alert_type, True)
        
        result = self.state_manager.check_trigger_conditions(task_id, 'agent1', alert_type, config)
        self.assertFalse(result['should_trigger'])  # 因为每个监测点只有1次异常，不足2次
    
    def test_default_behavior_compatibility(self):
        """测试默认配置下的向后兼容性"""
        task_id = 400
        alert_type = 'status'
        
        # 默认配置：1个监测点，连续1次异常即触发
        config = MockAlertConfig({
            'min_points': 1,
            'min_occurrences': 1,
            'trigger_mode': 'OR'
        })
        
        # 单个监测点单次异常应该触发告警
        self.state_manager.update_agent_state(task_id, 'agent1', alert_type, True)
        
        result = self.state_manager.check_trigger_conditions(task_id, 'agent1', alert_type, config)
        self.assertTrue(result['should_trigger'])
        self.assertEqual(result['trigger_type'], 'both')  # 同时满足连续次数和监测点数量

if __name__ == '__main__':
    unittest.main()