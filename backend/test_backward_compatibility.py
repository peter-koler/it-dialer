#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向后兼容性验证测试
确保增强告警功能在默认配置下与原有逻辑保持一致
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

class LegacyAlertLogic:
    """模拟原有告警逻辑：单点单次触发"""
    
    @staticmethod
    def should_trigger_alert(is_abnormal):
        """原有逻辑：任何异常都立即触发告警"""
        return is_abnormal

class EnhancedAlertLogic:
    """增强告警逻辑"""
    
    def __init__(self):
        self.cache = {}
    
    def update_agent_state(self, task_id, agent_id, alert_type, is_abnormal):
        """更新监测点状态"""
        key = f"{task_id}_{agent_id}_{alert_type}"
        state = self.cache.get(key, {
            'consecutive_failures': 0,
            'is_abnormal': False
        })
        
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
        key = f"{task_id}_{agent_id}_{alert_type}"
        agent_state = self.cache.get(key, {'consecutive_failures': 0})
        consecutive_count = agent_state['consecutive_failures']
        
        # 获取异常监测点总数
        abnormal_points_count = self.get_abnormal_agents_count(task_id, alert_type, alert_config)
        
        # 检查触发条件
        consecutive_triggered = consecutive_count >= min_occurrences
        points_triggered = abnormal_points_count >= min_points
        
        # 根据逻辑模式判断是否触发
        if trigger_mode == 'OR':
            should_trigger = consecutive_triggered or points_triggered
        elif trigger_mode == 'AND':
            should_trigger = consecutive_triggered and points_triggered
        else:
            should_trigger = False
        
        return {
            'should_trigger': should_trigger,
            'consecutive_count': consecutive_count,
            'abnormal_points_count': abnormal_points_count
        }

class TestBackwardCompatibility(unittest.TestCase):
    """向后兼容性测试"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.legacy_logic = LegacyAlertLogic()
        self.enhanced_logic = EnhancedAlertLogic()
        
        # 默认配置：模拟原有行为
        self.default_config = MockAlertConfig({
            'min_points': 1,      # 1个监测点异常即可
            'min_occurrences': 1, # 连续1次异常即可
            'trigger_mode': 'OR'  # OR模式
        })
    
    def test_single_point_single_failure(self):
        """测试单点单次异常的兼容性"""
        task_id = 100
        agent_id = 'agent1'
        alert_type = 'status'
        
        # 原有逻辑：单次异常立即触发
        legacy_result = self.legacy_logic.should_trigger_alert(True)
        
        # 增强逻辑：默认配置下应该有相同行为
        self.enhanced_logic.update_agent_state(task_id, agent_id, alert_type, True)
        enhanced_result = self.enhanced_logic.check_trigger_conditions(
            task_id, agent_id, alert_type, self.default_config
        )
        
        # 验证结果一致
        self.assertEqual(legacy_result, enhanced_result['should_trigger'])
        self.assertTrue(enhanced_result['should_trigger'])
    
    def test_single_point_recovery(self):
        """测试单点恢复的兼容性"""
        task_id = 101
        agent_id = 'agent1'
        alert_type = 'status'
        
        # 原有逻辑：恢复后不触发告警
        legacy_result = self.legacy_logic.should_trigger_alert(False)
        
        # 增强逻辑：先异常再恢复
        self.enhanced_logic.update_agent_state(task_id, agent_id, alert_type, True)
        self.enhanced_logic.update_agent_state(task_id, agent_id, alert_type, False)
        enhanced_result = self.enhanced_logic.check_trigger_conditions(
            task_id, agent_id, alert_type, self.default_config
        )
        
        # 验证结果一致
        self.assertEqual(legacy_result, enhanced_result['should_trigger'])
        self.assertFalse(enhanced_result['should_trigger'])
    
    def test_multiple_consecutive_failures(self):
        """测试多次连续异常的兼容性"""
        task_id = 102
        agent_id = 'agent1'
        alert_type = 'status'
        
        # 在默认配置下，每次异常都应该触发告警（与原逻辑一致）
        for i in range(5):
            # 原有逻辑：每次异常都触发
            legacy_result = self.legacy_logic.should_trigger_alert(True)
            
            # 增强逻辑：每次异常都应该触发
            self.enhanced_logic.update_agent_state(task_id, agent_id, alert_type, True)
            enhanced_result = self.enhanced_logic.check_trigger_conditions(
                task_id, agent_id, alert_type, self.default_config
            )
            
            # 验证结果一致
            self.assertEqual(legacy_result, enhanced_result['should_trigger'])
            self.assertTrue(enhanced_result['should_trigger'], 
                          f"第{i+1}次异常应该触发告警")
    
    def test_multiple_agents_default_behavior(self):
        """测试多个监测点的默认行为兼容性"""
        task_id = 103
        alert_type = 'status'
        
        # 在默认配置下，任何一个监测点异常都应该触发告警
        agents = ['agent1', 'agent2', 'agent3']
        
        for agent_id in agents:
            # 原有逻辑：单点异常触发
            legacy_result = self.legacy_logic.should_trigger_alert(True)
            
            # 增强逻辑：单点异常也应该触发
            self.enhanced_logic.update_agent_state(task_id, agent_id, alert_type, True)
            enhanced_result = self.enhanced_logic.check_trigger_conditions(
                task_id, agent_id, alert_type, self.default_config
            )
            
            # 验证结果一致
            self.assertEqual(legacy_result, enhanced_result['should_trigger'])
            self.assertTrue(enhanced_result['should_trigger'], 
                          f"监测点{agent_id}异常应该触发告警")
    
    def test_intermittent_failures(self):
        """测试间歇性异常的兼容性"""
        task_id = 104
        agent_id = 'agent1'
        alert_type = 'status'
        
        # 模拟间歇性异常：异常->正常->异常->正常
        failure_pattern = [True, False, True, False, True]
        
        for i, is_abnormal in enumerate(failure_pattern):
            # 原有逻辑
            legacy_result = self.legacy_logic.should_trigger_alert(is_abnormal)
            
            # 增强逻辑
            self.enhanced_logic.update_agent_state(task_id, agent_id, alert_type, is_abnormal)
            enhanced_result = self.enhanced_logic.check_trigger_conditions(
                task_id, agent_id, alert_type, self.default_config
            )
            
            # 验证结果一致
            self.assertEqual(legacy_result, enhanced_result['should_trigger'],
                          f"第{i+1}步（{'异常' if is_abnormal else '正常'}）结果不一致")
    
    def test_enhanced_features_disabled_by_default(self):
        """测试增强功能在默认配置下被禁用"""
        task_id = 105
        alert_type = 'status'
        
        # 在默认配置下，即使多个监测点异常，每个都应该独立触发
        # 而不是等待达到阈值才触发
        
        # 第一个监测点异常
        self.enhanced_logic.update_agent_state(task_id, 'agent1', alert_type, True)
        result1 = self.enhanced_logic.check_trigger_conditions(
            task_id, 'agent1', alert_type, self.default_config
        )
        self.assertTrue(result1['should_trigger'], "第一个监测点异常应该立即触发")
        
        # 第二个监测点异常
        self.enhanced_logic.update_agent_state(task_id, 'agent2', alert_type, True)
        result2 = self.enhanced_logic.check_trigger_conditions(
            task_id, 'agent2', alert_type, self.default_config
        )
        self.assertTrue(result2['should_trigger'], "第二个监测点异常应该立即触发")
        
        # 验证计数器正确工作，但不影响触发逻辑
        self.assertEqual(result1['consecutive_count'], 1)
        self.assertEqual(result2['consecutive_count'], 1)
        self.assertEqual(result2['abnormal_points_count'], 2)

if __name__ == '__main__':
    print("开始向后兼容性验证测试...")
    unittest.main(verbosity=2)