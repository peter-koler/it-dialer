from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json
import logging
from app import db
from app.models.alert import AlertConfig

logger = logging.getLogger(__name__)


class AlertStateManager:
    """
    告警状态管理器
    负责维护监测点的连续异常状态和历史记录
    """
    
    def __init__(self):
        self.logger = logger
        # 内存缓存：{task_id: {agent_id: {alert_type: state}}}
        self._memory_cache = {}
        # 缓存过期时间（小时）
        self.cache_expire_hours = 24
    
    def get_agent_state(self, task_id: int, agent_id: str, alert_type: str) -> Dict[str, Any]:
        """
        获取监测点的告警状态
        
        Args:
            task_id: 任务ID
            agent_id: 监测点ID
            alert_type: 告警类型
            
        Returns:
            Dict: 状态信息
        """
        if task_id not in self._memory_cache:
            self._memory_cache[task_id] = {}
        
        if agent_id not in self._memory_cache[task_id]:
            self._memory_cache[task_id][agent_id] = {}
        
        if alert_type not in self._memory_cache[task_id][agent_id]:
            self._memory_cache[task_id][agent_id][alert_type] = {
                'consecutive_failures': 0,
                'last_status': 'normal',
                'last_update': datetime.now(),
                'history': []  # 保存最近10次检测结果
            }
        
        return self._memory_cache[task_id][agent_id][alert_type]
    
    def update_agent_state(self, task_id: int, agent_id: str, alert_type: str, 
                          is_abnormal: bool, result_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        更新监测点的告警状态
        
        Args:
            task_id: 任务ID
            agent_id: 监测点ID
            alert_type: 告警类型
            is_abnormal: 是否异常
            result_data: 结果数据
            
        Returns:
            Dict: 更新后的状态信息
        """
        state = self.get_agent_state(task_id, agent_id, alert_type)
        
        # 更新连续异常计数
        if is_abnormal:
            if state['last_status'] == 'abnormal':
                state['consecutive_failures'] += 1
            else:
                state['consecutive_failures'] = 1
            state['last_status'] = 'abnormal'
        else:
            state['consecutive_failures'] = 0
            state['last_status'] = 'normal'
        
        # 更新时间戳
        state['last_update'] = datetime.now()
        
        # 更新历史记录（保留最近10次）
        history_item = {
            'timestamp': datetime.now().isoformat(),
            'status': 'abnormal' if is_abnormal else 'normal',
            'consecutive_count': state['consecutive_failures']
        }
        
        if result_data:
            history_item['result_data'] = result_data
        
        state['history'].append(history_item)
        if len(state['history']) > 10:
            state['history'] = state['history'][-10:]
        
        self.logger.debug(f"更新告警状态 - 任务:{task_id}, 监测点:{agent_id}, 类型:{alert_type}, "
                         f"异常:{is_abnormal}, 连续次数:{state['consecutive_failures']}")
        
        return state
    
    def get_abnormal_agents_count(self, task_id: int, alert_type: str, 
                                 alert_config: AlertConfig) -> int:
        """
        获取当前异常的监测点数量
        
        Args:
            task_id: 任务ID
            alert_type: 告警类型
            alert_config: 告警配置
            
        Returns:
            int: 异常监测点数量
        """
        if task_id not in self._memory_cache:
            return 0
        
        config = alert_config.get_config()
        min_occurrences = config.get('min_occurrences', 1)
        
        abnormal_count = 0
        for agent_id, agent_states in self._memory_cache[task_id].items():
            if alert_type in agent_states:
                state = agent_states[alert_type]
                # 检查是否满足连续次数阈值
                if state['consecutive_failures'] >= min_occurrences:
                    abnormal_count += 1
        
        return abnormal_count
    
    def check_trigger_conditions(self, task_id: int, agent_id: str, alert_type: str, 
                               alert_config: AlertConfig) -> Dict[str, Any]:
        """
        检查告警触发条件
        
        Args:
            task_id: 任务ID
            agent_id: 监测点ID
            alert_type: 告警类型
            alert_config: 告警配置
            
        Returns:
            Dict: 触发检查结果
        """
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
            'trigger_value': None,
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
                    result['trigger_value'] = f"连续{consecutive_count}次异常且{abnormal_points_count}个监测点异常"
                elif consecutive_triggered:
                    result['trigger_type'] = 'consecutive'
                    result['trigger_value'] = f"连续{consecutive_count}次异常"
                else:
                    result['trigger_type'] = 'point_count'
                    result['trigger_value'] = f"{abnormal_points_count}个监测点异常"
        
        elif trigger_mode == 'AND':
            if consecutive_triggered and points_triggered:
                result['should_trigger'] = True
                result['trigger_type'] = 'both'
                result['trigger_value'] = f"连续{consecutive_count}次异常且{abnormal_points_count}个监测点异常"
        
        self.logger.debug(f"告警触发检查 - 任务:{task_id}, 监测点:{agent_id}, 类型:{alert_type}, "
                         f"结果:{result}")
        
        return result
    
    def cleanup_expired_cache(self):
        """
        清理过期的缓存数据
        """
        expire_time = datetime.now() - timedelta(hours=self.cache_expire_hours)
        
        for task_id in list(self._memory_cache.keys()):
            for agent_id in list(self._memory_cache[task_id].keys()):
                for alert_type in list(self._memory_cache[task_id][agent_id].keys()):
                    state = self._memory_cache[task_id][agent_id][alert_type]
                    if state['last_update'] < expire_time:
                        del self._memory_cache[task_id][agent_id][alert_type]
                
                # 如果监测点没有任何告警类型，删除监测点
                if not self._memory_cache[task_id][agent_id]:
                    del self._memory_cache[task_id][agent_id]
            
            # 如果任务没有任何监测点，删除任务
            if not self._memory_cache[task_id]:
                del self._memory_cache[task_id]
        
        self.logger.info("清理过期告警状态缓存完成")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            Dict: 缓存统计信息
        """
        total_tasks = len(self._memory_cache)
        total_agents = sum(len(agents) for agents in self._memory_cache.values())
        total_states = sum(
            len(states) 
            for agents in self._memory_cache.values() 
            for states in agents.values()
        )
        
        return {
            'total_tasks': total_tasks,
            'total_agents': total_agents,
            'total_states': total_states,
            'cache_size_mb': len(str(self._memory_cache)) / 1024 / 1024
        }


# 全局实例
alert_state_manager = AlertStateManager()