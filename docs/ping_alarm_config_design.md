# Ping任务告警配置设计文档

## 1. 数据结构分析

### Ping任务返回数据结构
基于agent/plugins/ping.py的实现，ping任务返回以下关键字段：

```json
{
  "status": "success|failed|error|timeout",
  "packet_sent": 4,
  "packet_received": 4,
  "packet_loss": 0.0,
  "rtt_min": 10.0,
  "rtt_avg": 15.5,
  "rtt_max": 20.0,
  "execution_time": 2.5,
  "target": "8.8.8.8",
  "message": "错误信息（如果有）"
}
```

## 2. 告警配置结构设计

### 2.1 整体配置结构
参考HTTP任务的alarm_config结构，设计ping任务的告警配置：

```json
{
  "enabled": true,
  "rules": {
    "status": {
      "enabled": true,
      "condition": "异常",
      "level": "warning"
    },
    "packet_loss": {
      "enabled": true,
      "condition": "gt",
      "value": 10.0,
      "level": "critical"
    },
    "execution_time": {
      "enabled": true,
      "condition": "gt",
      "value": 5000,
      "level": "warning"
    }
  }
}
```

### 2.2 各告警规则详细说明

#### 2.2.1 状态告警 (status)
- **enabled**: 是否启用状态告警
- **condition**: 触发条件
  - "异常": 当status为failed、error、timeout时触发
  - "正常": 当status为success时触发
- **level**: 告警级别 (info/warning/critical)

#### 2.2.2 丢包率告警 (packet_loss)
- **enabled**: 是否启用丢包率告警
- **condition**: 比较条件
  - "gt": 大于阈值时触发
  - "gte": 大于等于阈值时触发
  - "eq": 等于阈值时触发
- **value**: 阈值（百分比，0-100）
- **level**: 告警级别 (info/warning/critical)

#### 2.2.3 执行时间告警 (execution_time)
- **enabled**: 是否启用执行时间告警
- **condition**: 比较条件
  - "gt": 大于阈值时触发
  - "gte": 大于等于阈值时触发
  - "lt": 小于阈值时触发
  - "lte": 小于等于阈值时触发
- **value**: 阈值（毫秒）
- **level**: 告警级别 (info/warning/critical)

## 3. 告警类型定义

### 3.1 告警类型标识
- `ping_status`: Ping状态告警
- `ping_packet_loss`: Ping丢包率告警
- `ping_execution_time`: Ping执行时间告警

### 3.2 告警级别
- `info`: 信息级别
- `warning`: 警告级别
- `critical`: 严重级别

## 4. 实现要点

### 4.1 后端实现
1. 在alert_matcher.py中添加`_check_ping_alarm_config_alerts`方法
2. 实现三个具体的检查方法：
   - `_check_ping_status_alert`
   - `_check_ping_packet_loss_alert`
   - `_check_ping_execution_time_alert`
3. 在主流程中调用ping告警检查

### 4.2 前端实现
1. 在任务编辑页面为ping类型任务添加告警配置面板
2. 参考HTTP告警配置UI设计
3. 支持三种告警规则的独立配置

### 4.3 数据库
- 使用现有的Task.alarm_config字段存储配置
- 使用现有的Alert表存储告警记录
- 无需修改数据库结构

## 5. 配置示例

### 5.1 基础配置示例
```json
{
  "enabled": true,
  "rules": {
    "status": {
      "enabled": true,
      "condition": "异常",
      "level": "critical"
    },
    "packet_loss": {
      "enabled": true,
      "condition": "gt",
      "value": 5.0,
      "level": "warning"
    },
    "execution_time": {
      "enabled": false
    }
  }
}
```

### 5.2 完整配置示例
```json
{
  "enabled": true,
  "rules": {
    "status": {
      "enabled": true,
      "condition": "异常",
      "level": "critical"
    },
    "packet_loss": {
      "enabled": true,
      "condition": "gt",
      "value": 10.0,
      "level": "critical"
    },
    "execution_time": {
      "enabled": true,
      "condition": "gt",
      "value": 3000,
      "level": "warning"
    }
  }
}
```

## 6. 兼容性说明

- 配置结构与HTTP告警保持一致，便于前端复用组件
- 使用现有的数据库字段和表结构
- 不影响现有的HTTP和API告警功能
- 支持渐进式启用，可以只启用部分告警规则