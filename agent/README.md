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
│   ├── http_plugin.py   # HTTP拨测插件，支持DNS解析时间、连接时间、SSL握手时间、首字节时间、下载时间等指标
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
- 支持变量提取和传递（JSONPath、正则表达式）
- 支持断言验证（状态码、响应时间、响应内容）
- 支持各种HTTP方法（GET、POST、PUT、DELETE等）
- 支持请求头、认证、SSL配置
- 支持V2格式的认证配置（OAuth1, OAuth2, Bearer Token等）
- 支持从服务器获取系统变量（$public_开头）

#### 3.4 HTTP插件 (http_plugin.py)
执行HTTP/HTTPS拨测任务，支持完整请求链路分析。
- 支持DNS解析时间测量
- 支持TCP连接时间测量
- 支持SSL握手时间测量
- 支持首字节时间测量
- 支持下载时间测量
- 支持重定向跟踪
- 支持SSL证书验证跳过
- 支持自定义请求头和超时设置

插件接口规范：
每个插件必须实现：
- [PLUGIN_NAME](file:///Users/peter/Documents/code/boce/it-dialer/agent/plugins/api.py#L18-L18): 插件名称常量
- [execute(task)](file:///Users/peter/Documents/code/boce/it-dialer/agent/plugins/api.py#L33-L203): 任务执行函数，接收任务配置，返回执行结果
  - 任务参数格式：
    {
      "task_id": "任务ID",
      "type": "插件名称",
      "target": "目标地址",
      "config": { /* 插件特定配置 */ },
      "params": { /* 其他参数 */ }
    }

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
   - 支持V2格式的initialVariables配置
   - 支持多步骤任务的变量传递
   - 支持步骤级fail_fast配置（失败后立即中止）
   - 支持断言触发告警
   - 新增SSL握手时间统计
   - 新增下载时间统计

## API交互

Agent与后端服务器通过RESTful API进行交互：

### 注册接口
- `POST /api/v1/nodes/register`: 注册Agent信息

### 心跳接口
- `POST /api/v1/nodes/heartbeat`: 发送心跳包

### 任务接口
- `GET /api/v1/tasks?agent_id={agent_id}`: 获取分配给当前agent的任务列表，支持agent_id过滤

### 结果接口
- `POST /api/v1/results`: 上报任务执行结果

## 部署和运行

### 环境要求
- Python 3.6+
- 依赖包：
  - requests>=2.28.0
  - jsonpath-ng>=1.5.3
  - dnspython>=2.2.0  # 新增，用于DNS解析
  - requests-oauthlib>=1.3.1  # 新增，用于OAuth认证
  - urllib3>=1.26.9  # 新增，用于HTTP连接管理

### 安装依赖
```
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
```
python agent.py
```

## 扩展性

### 添加新插件
1. 在plugins/目录创建新插件文件
2. 实现PLUGIN_NAME常量和execute()函数
3. execute()函数必须接收任务字典参数，返回结果字典
4. 插件会自动被加载和识别
5. 建议实现完整的错误处理和日志记录

### 配置管理
- 通过 [agent_config.json](agent_config.json) 配置Agent行为
- 通过后端管理系统配置拨测任务

## 日志和监控

Agent使用Python标准日志模块记录运行信息：
- INFO级别：记录重要操作和状态
- ERROR级别：记录错误和异常
- DEBUG级别：记录详细调试信息

### 系统变量支持
Agent在执行API任务时，会自动从服务器获取系统变量（$public_开头），这些变量可在任务中使用：
1. 在任务配置中使用$public_var_name格式引用变量
2. 变量值从服务器API获取
3. 支持变量的自动替换

## 故障处理

- DNS解析失败：记录DNS错误信息
- SSL握手失败：记录SSL错误详情
- HTTP重定向：支持自动跟踪
- 证书验证：开发环境跳过验证
- 响应处理：支持JSON和文本响应
