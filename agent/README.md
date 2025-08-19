# IT拨测系统Agent说明文档

## 项目概述

IT拨测系统Agent是一个分布式的网络拨测客户端，负责执行各种网络测试任务（如Ping、TCP连接、API测试等），并将结果上报给后端服务器。Agent支持插件化架构，可以动态加载不同类型的拨测插件。

## 项目结构

```
agent/
├── agent.py              # Agent主程序
├── agent_config.json     # Agent配置文件
├── config/               # 任务配置模块
│   └── tasks.py         # 任务配置管理
├── management/           # 任务管理模块
│   └── tasks.py         # 任务结果管理
├── plugins/              # 拨测插件目录
│   ├── api.py           # API拨测插件
│   ├── ping.py          # Ping拨测插件
│   └── tcp.py           # TCP拨测插件
```

## 核心组件说明

### 1. Agent主程序 (agent.py)

这是Agent的核心组件，负责：
- 加载配置文件
- 注册和管理Agent信息
- 发送心跳包到服务器
- 从服务器获取拨测任务
- 执行拨测任务
- 上报执行结果到服务器
- 管理插件加载和执行

主要功能方法：
- `collect_agent_info()`: 收集Agent信息（ID、区域、IP、主机名）
- `load_plugins()`: 动态加载拨测插件
- `register_agent()`: 向服务器注册Agent
- `send_heartbeat()`: 发送心跳信息
- `get_tasks()`: 从服务器获取任务列表
- `execute_task()`: 执行单个拨测任务
- `report_result()`: 上报任务执行结果

### 2. 配置文件 (agent_config.json)

Agent的配置文件，包含以下主要配置项：
- `agent_id`: Agent唯一标识符
- `server_url`: 后端服务器地址
- `plugins_dir`: 插件目录路径
- `report_interval`: 上报间隔（秒）
- `log_level`: 日志级别
- `agent_area`: Agent所在区域

### 3. 插件系统 (plugins/)

Agent支持插件化架构，每个插件实现特定类型的拨测任务。

#### 3.1 Ping插件 (ping.py)
执行ICMP Ping测试，检测网络连通性和延迟。
- 支持Windows和Linux系统
- 可配置Ping次数
- 返回丢包率、最小/平均/最大延迟等指标

#### 3.2 TCP插件 (tcp.py)
执行TCP端口连通性测试。
- 测试指定主机和端口的可达性
- 可配置超时时间
- 返回连接状态和响应时间

#### 3.3 API插件 (api.py)
执行复杂的API拨测任务，支持多步骤事务。
- 支持多步骤HTTP请求
- 支持变量提取和传递
- 支持断言验证
- 支持各种HTTP方法（GET、POST、PUT、DELETE等）
- 支持请求头、认证、SSL等配置

插件接口规范：
每个插件必须实现：
- `PLUGIN_NAME`: 插件名称常量
- `execute(task)`: 任务执行函数，接收任务配置，返回执行结果

### 4. 任务配置模块 (config/tasks.py)

提供本地任务配置管理功能：
- 加载和保存任务配置
- 添加、更新、删除任务
- 根据ID或类型查询任务

### 5. 任务管理模块 (management/tasks.py)

管理任务执行结果：
- 存储和查询任务执行结果
- 按任务ID或时间范围筛选结果
- 格式化结果用于显示

## 工作流程

1. **启动阶段**
   - 加载配置文件
   - 收集Agent信息
   - 加载拨测插件
   - 向服务器注册Agent

2. **运行阶段**
   - 启动心跳线程，定期发送心跳包
   - 定期从服务器获取任务列表
   - 根据任务配置执行拨测任务
   - 上报执行结果到服务器

3. **任务执行**
   - 根据任务类型调用相应插件
   - 插件执行具体拨测操作
   - 收集执行结果和指标
   - 返回标准化结果格式

## API交互

Agent与后端服务器通过RESTful API进行交互：

### 注册接口
- `POST /api/v1/nodes/register`: 注册Agent信息

### 心跳接口
- `POST /api/v1/nodes/heartbeat`: 发送心跳包

### 任务接口
- `GET /api/v1/tasks`: 获取拨测任务列表

### 结果接口
- `POST /api/v1/results`: 上报任务执行结果

## 部署和运行

### 环境要求
- Python 3.6+
- 依赖包：requests, jsonpath_ng

### 安装依赖
```bash
pip install requests jsonpath_ng
```

### 配置Agent
编辑 [agent_config.json](agent_config.json) 文件：
```json
{
  "agent_id": "unique_agent_id",
  "server_url": "http://localhost:5000",
  "plugins_dir": "plugins",
  "report_interval": 60,
  "log_level": "INFO",
  "agent_area": "guangzhou"
}
```

### 运行Agent
```bash
python agent.py
```

## 扩展性

### 添加新插件
1. 在 [plugins/](plugins/) 目录下创建新的插件文件
2. 实现 `PLUGIN_NAME` 常量和 `execute()` 函数
3. 插件会自动被加载和识别

### 配置管理
- 通过 [agent_config.json](agent_config.json) 配置Agent行为
- 通过后端管理系统配置拨测任务

## 日志和监控

Agent使用Python标准日志模块记录运行信息：
- INFO级别：记录重要操作和状态
- ERROR级别：记录错误和异常
- DEBUG级别：记录详细调试信息

## 故障处理

- 网络异常：自动重试机制
- 任务执行失败：记录详细错误信息并上报
- 服务器连接失败：继续尝试连接并缓存结果