#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强告警功能测试
测试连续次数统计、监测点数量统计和不同逻辑模式的告警触发
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.alert_state_manager import AlertStateManager
from app.services.alert_matcher import AlertMatcher
from app.models.alert import AlertConfig, Alert


class TestEnhancedAlert(unittest.TestCase):
    """增强告警功能测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.state_manager = AlertStateManager()
        self.alert_matcher = AlertMatcher()
        
        # 清理缓存
        self.state_manager._memory_cache.clear()
        
        # 模拟告警配置
        self.alert_config = Mock(spec=AlertConfig)
        self.alert_config.id = 1
        self.alert_config.task_id = 100
        self.alert_config.min_points = 2
        self.alert_config.min_occurrences = 3
        self.alert_config.trigger_mode = 'AND'
        self.alert_config.enabled = True
        self.alert_config.level = 'warning'
        self.alert_config.get_config.return_value = {
            'min_points': 2,
            'min_occurrences': 3,
            'trigger_mode': 'AND'
        }
        
    def tearDown(self):
        """测试后清理"""
        self.state_manager._memory_cache.clear()
    
    def test_single_point_consecutive_occurrences(self):
        """测试单个监测点的连续次数统计"""
        task_id = 100
        agent_id = 'agent1'
        
        alert_type = 'status'
        
        # 第一次异常
        state = self.state_manager.update_agent_state(task_id, agent_id, alert_type, True)
        self.assertEqual(state['consecutive_failures'], 1)
        
        # 第二次异常
        state = self.state_manager.update_agent_state(task_id, agent_id, alert_type, True)
        self.assertEqual(state['consecutive_failures'], 2)
        
        # 第三次异常
        state = self.state_manager.update_agent_state(task_id, agent_id, alert_type, True)
        self.assertEqual(state['consecutive_failures'], 3)
        
        # 一次正常，重置计数
        state = self.state_manager.update_agent_state(task_id, agent_id, alert_type, False)
        self.assertEqual(state['consecutive_failures'], 0)
    
    def test_multiple_points_abnormal_count(self):
        """测试多个监测点的异常数量统计"""
        task_id = 100
        alert_type = 'status'
        
        # 两个监测点异常
        self.state_manager.update_agent_state(task_id, 'agent1', alert_type, True)
        self.state_manager.update_agent_state(task_id, 'agent2', alert_type, True)
        self.state_manager.update_agent_state(task_id, 'agent3', alert_type, False)
        
        abnormal_count = self.state_manager.get_abnormal_agents_count(task_id, alert_type, self.alert_config)
        self.assertEqual(abnormal_count, 2)
        
        # 再增加一个异常监测点
        self.state_manager.update_agent_state(task_id, 'agent3', alert_type, True)
        abnormal_count = self.state_manager.get_abnormal_agents_count(task_id, alert_type, self.alert_config)
        self.assertEqual(abnormal_count, 3)
    
    def test_and_trigger_mode(self):
        """测试AND逻辑模式：需要同时满足监测点数量和连续次数阈值"""
        task_id = 200
        
        # 设置为AND模式
        self.alert_config.get_config.return_value = {
            'min_points': 2,
            'min_occurrences': 3,
            'trigger_mode': 'AND'
        }
        
        alert_type = 'status'
        
        # 只有1个监测点连续3次异常 - 不应触发
        for _ in range(3):
            self.state_manager.update_agent_state(task_id, 'agent1', alert_type, True)
        
        result = self.state_manager.check_trigger_conditions(
            task_id, 'agent1', alert_type, self.alert_config
        )
        self.assertFalse(result['should_trigger'])
        
        # 2个监测点，但只连续2次异常 - 不应触发
        self.state_manager.update_agent_state(task_id, 'agent2', alert_type, True)
        self.state_manager.update_agent_state(task_id, 'agent2', alert_type, True)
        
        result = self.state_manager.check_trigger_conditions(
            task_id, 'agent2', alert_type, self.alert_config
        )
        self.assertFalse(result['should_trigger'])
        
        # 2个监测点，且都连续3次异常 - 应该触发
        self.state_manager.update_agent_state(task_id, 'agent2', alert_type, True)
        
        result = self.state_manager.check_trigger_conditions(
            task_id, 'agent2', alert_type, self.alert_config
        )
        self.assertTrue(result['should_trigger'])
    
    def test_or_trigger_mode(self):
        """测试OR逻辑模式：满足监测点数量或连续次数阈值任一条件即可"""
        task_id = 300
        
        # 设置为OR模式
        self.alert_config.get_config.return_value = {
            'min_points': 3,
            'min_occurrences': 2,
            'trigger_mode': 'OR'
        }
        
        alert_type = 'status'
        
        # 只有1个监测点连续2次异常 - 应该触发（满足连续次数条件）
        self.state_manager.update_agent_state(task_id, 'agent1', alert_type, True)
        self.state_manager.update_agent_state(task_id, 'agent1', alert_type, True)
        
        result = self.state_manager.check_trigger_conditions(
            task_id, 'agent1', alert_type, self.alert_config
        )
        self.assertTrue(result['should_trigger'])
        
        # 清理状态，重新测试
        self.state_manager._memory_cache.clear()
        
        # 3个监测点异常，但只连续1次 - 应该触发（满足监测点数量条件）
        self.state_manager.update_agent_state(task_id, 'agent1', alert_type, True)
        self.state_manager.update_agent_state(task_id, 'agent2', alert_type, True)
        self.state_manager.update_agent_state(task_id, 'agent3', alert_type, True)
        
        result = self.state_manager.check_trigger_conditions(
            task_id, 'agent1', alert_type, self.alert_config
        )
        self.assertTrue(result['should_trigger'])
    
    def test_default_behavior_compatibility(self):
        """测试默认配置下的向后兼容性"""
        task_id = 400
        
        # 默认配置：1个监测点，连续1次异常即触发
        self.alert_config.get_config.return_value = {
            'min_points': 1,
            'min_occurrences': 1,
            'trigger_mode': 'OR'
        }
        
        alert_type = 'status'
        
        # 单个监测点单次异常应该触发告警
        self.state_manager.update_agent_state(task_id, 'agent1', alert_type, True)
        
        result = self.state_manager.check_trigger_conditions(
            task_id, 'agent1', alert_type, self.alert_config
        )
        self.assertTrue(result['should_trigger'])
    
    def test_cache_cleanup(self):
        """测试缓存清理功能"""
        task_id = 100
        agent_id = 'agent1'
        
        alert_type = 'status'
        
        # 添加一些状态数据
        self.state_manager.update_agent_state(task_id, agent_id, alert_type, True)
        
        # 验证数据存在
        self.assertTrue(len(self.state_manager._memory_cache) > 0)
        
        # 清理缓存
        self.state_manager.cleanup_expired_cache(max_age_hours=0)
        
        # 验证缓存已清理
        self.assertEqual(len(self.state_manager._memory_cache), 0)
    
    @patch('app.models.alert.Alert')
    def test_enhanced_alert_integration(self, mock_alert_class):
        """测试增强告警的完整集成流程"""
        # 模拟结果数据
        result_data = {
            'task_id': 100,
            'agent_id': 'agent1',
            'status': 'failed',
            'details': {'error': 'Connection timeout'}
        }
        
        # 模拟告警配置
        mock_config = Mock()
        mock_config.id = 1
        mock_config.task_id = 100
        mock_config.min_points = 1
        mock_config.min_occurrences = 2
        mock_config.trigger_mode = 'OR'
        mock_config.enabled = True
        mock_config.level = 'warning'
        
        # 模拟数据库查询
        with patch('app.models.alert.AlertConfig.query') as mock_query:
            mock_query.filter_by.return_value.all.return_value = [mock_config]
            
            # 第一次异常 - 不应触发告警
            alerts = self.alert_matcher._check_enhanced_alert(
                result_data, mock_config
            )
            self.assertEqual(len(alerts), 0)
            
            # 第二次异常 - 应该触发告警
            alerts = self.alert_matcher._check_enhanced_alert(
                result_data, mock_config
            )
            self.assertEqual(len(alerts), 1)
    
    def test_edge_cases(self):
        """测试边界情况"""
        task_id = 100
        
        # 测试配置为0的情况
        self.alert_config.min_points = 0
        self.alert_config.min_occurrences = 0
        
        should_trigger = self.state_manager.should_trigger_alert(
            task_id, self.alert_config
        )
        self.assertFalse(should_trigger)
        
        # 设置极高的阈值
        self.alert_config.get_config.return_value = {
            'min_points': 1000,
            'min_occurrences': 1000,
            'trigger_mode': 'OR'
        }
        
        alert_type = 'status'
        
        # 添加少量异常数据
        self.state_manager.update_agent_state(task_id, 'agent1', alert_type, True)
        
        result = self.state_manager.check_trigger_conditions(
            task_id, 'agent1', alert_type, self.alert_config
        )
        self.assertFalse(result['should_trigger'])


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)