# IT拨测系统Agent说明文档

## 项目概述

IT拨测系统Agent是一个分布式的网络拨测客户端，负责执行各种网络测试任务（如Ping、TCP连接、API测试等），并将结果上报给后端服务器。Agent支持多租户架构，不同租户之间数据完全隔离，且每个租户可以独立配置自己的拨测任务和参数。

## 项目结构

## 核心组件说明

### 1. Agent主程序 (agent.py)

这是Agent的核心组件，负责：
- 加载配置文件
- 注册和管理Agent信息
- 发送心跳包到服务器
- 从服务器获取任务列表，支持租户隔离
- 执行拨测任务
- 上报执行结果到服务器，包含租户ID
- 管理插件加载和执行

主要功能方法：
- [collect_agent_info()](file:///Users/peter/Documents/code/boce/it-dialer/agent/agent.py#L64-L72): 收集Agent信息（ID、区域、IP、主机名）
- [load_plugins()](file:///Users/peter/Documents/code/boce/it-dialer/agent/agent.py#L119-L153): 动态加载拨测插件
- [register_agent()](file:///Users/peter/Documents/code/boce/it-dialer/agent/agent.py#L155-L188): 向服务器注册Agent，支持认证
- [send_heartbeat()](file:///Users/peter/Documents/code/boce/it-dialer/agent/agent.py#L225-L261): 发送心跳信息，支持认证
- [get_tasks()](file:///Users/peter/Documents/code/boce/it-dialer/agent/agent.py#L285-L365): 从服务器获取分配给当前agent的任务，支持租户过滤
- [execute_task()](file:///Users/peter/Documents/code/boce/it-dialer/agent/agent.py#L367-L431): 执行拨测任务，支持多步骤事务、变量传递、断言验证
- [report_result()](file:///Users/peter/Documents/code/boce/it-dialer/agent/agent.py#L433-L485): 上报任务执行结果，包含租户ID

### 2. 配置文件 (agent_config.json)

Agent的配置文件，包含以下主要配置项：
- [agent_id](file:///Users/peter/Documents/code/boce/it-dialer/backend/app/models/node.py#L0-L0): Agent唯一标识符
- `server_url`: 后端服务器地址
- `plugins_dir`: 插件目录路径
- `report_interval`: 上报间隔（秒）
- [log_level](file:///Users/peter/Documents/code/boce/it-dialer/backend/logging_config.py#L0-L0): 日志级别
- [agent_area](file:///Users/peter/Documents/code/boce/it-dialer/backend/app/models/node.py#L0-L0): Agent所在区域
- `api_token`: API认证token，用于多租户环境
- `auth_required`: 是否启用认证

示例配置：
```json
{
  "agent_id": "book",
  "server_url": "http://localhost:5001",
  "plugins_dir": "plugins",
  "report_interval": 60,
  "log_level": "INFO",
  "agent_area": "guangzhou",
  "api_token": "agent-default-token-2024",
  "auth_required": true
}
3. 插件系统 (plugins/)
Agent支持插件化架构，每个插件实现特定类型的拨测任务。

3.1 Ping插件 (ping.py)
执行ICMP Ping测试，检测网络连通性和延迟。

支持Windows和Linux系统
可配置Ping次数
返回丢包率、最小/平均/最大延迟等指标
支持多租户环境下的任务隔离
3.2 TCP插件 (tcp.py)
执行TCP端口连通性测试。

测试指定主机和端口的可达性
可配置超时时间
返回连接状态和响应时间
支持多租户环境下的任务隔离
3.3 API插件 (api.py)
执行复杂的API拨测任务，支持多步骤事务。

支持多步骤HTTP请求
支持变量提取和传递（JSONPath、正则表达式）
支持断言验证（状态码、响应时间、响应内容）
支持各种HTTP方法（GET、POST、PUT、DELETE等）
支持请求头、认证、SSL配置
支持V2格式的认证配置（OAuth1, OAuth2, Bearer Token等）
支持从服务器获取系统变量（$public_开头）
支持多租户环境下的变量隔离
3.4 HTTP插件 (http_plugin.py)
执行HTTP/HTTPS拨测任务，支持完整请求链路分析。

支持DNS解析时间测量
支持TCP连接时间测量
支持SSL握手时间测量
支持首字节时间测量
支持下载时间测量
支持重定向跟踪
支持SSL证书验证跳过
支持自定义请求头和超时设置
支持多租户环境下的任务隔离
插件接口规范： 每个插件必须实现：

PLUGIN_NAME: 插件名称常量
execute(task): 任务执行函数，接收任务配置，返回执行结果
任务参数格式： { "task_id": "任务ID", "type": "插件名称", "target": "目标地址", "config": { /* 插件特定配置 / }, "params": { / 其他参数 */ }, "tenant_id": "租户ID" }
4. 任务配置模块 (config/tasks.py)
提供本地任务配置管理功能：

加载和保存任务配置
添加、更新、删除任务
根据ID或类型查询任务
支持多租户任务配置
5. 任务管理模块 (management/tasks.py)
管理任务执行结果：

存储和查询任务执行结果
按任务ID或时间范围筛选结果
格式化结果用于显示
支持多租户任务结果隔离
工作流程
启动阶段

加载配置文件
收集Agent信息
加载拨测插件
向服务器注册Agent，包含认证token
更新Agent信息
运行阶段

启动心跳线程，定期发送心跳包
定期从服务器获取任务列表，支持租户过滤
根据任务配置执行拨测任务
上报执行结果到服务器，包含租户ID
任务执行

支持V2格式的initialVariables配置
支持多步骤任务的变量传递
支持步骤级fail_fast配置（失败后立即中止）
支持断言触发告警
新增SSL握手时间统计
新增下载时间统计
支持多租户任务执行
API交互
Agent与后端服务器通过RESTful API进行交互：

注册接口
POST /api/v1/nodes/register: 注册Agent信息，包含租户信息
心跳接口
POST /api/v1/nodes/heartbeat: 发送心跳包，包含认证token
任务接口
GET /api/v1/tasks/agent?agent_id={agent_id}: 获取分配给当前agent的任务列表，支持agent_id过滤和租户隔离
GET /api/v1/tasks/agent?enabled=true&agent_id={agent_id}: 获取启用的任务列表
结果接口
POST /api/v1/results: 上报任务执行结果，包含租户ID
POST /api/v1/results?tenant_id={tenant_id}: 支持租户隔离的结果上报
部署和运行
环境要求
Python 3.6+
依赖包：
requests>=2.28.0
jsonpath-ng>=1.5.3
dnspython>=2.2.0 # 新增，用于DNS解析
requests-oauthlib>=1.3.1 # 新增，用于OAuth认证
urllib3>=1.26.9 # 新增，用于HTTP连接管理
安装依赖
pip install requests jsonpath_ng dnspython requests-oauthlib urllib3
{
  "agent_id": "unique_agent_id",
  "server_url": "http://localhost:5000",
  "plugins_dir": "plugins",
  "report_interval": 60,
  "log_level": "INFO",
  "agent_area": "guangzhou",
  "api_token": "agent-default-token-2024",  # API认证token
  "auth_required": true  # 是否启用认证
}
python agent.py
扩展性
添加新插件
在plugins/目录创建新插件文件
实现PLUGIN_NAME常量和execute()函数
execute()函数必须接收任务字典参数，返回结果字典
插件会自动被加载和识别
建议实现完整的错误处理和日志记录
配置管理
通过 agent_config.json 配置Agent行为
通过后端管理系统配置拨测任务
支持多租户配置管理
支持租户隔离的任务执行
日志和监控
Agent使用Python标准日志模块记录运行信息：

INFO级别：记录重要操作和状态
ERROR级别：记录错误和异常
DEBUG级别：记录详细调试信息
系统变量支持
Agent在执行API任务时，会自动从服务器获取系统变量（$public_开头），这些变量可在任务中使用：

在任务配置中使用$public_var_name格式引用变量
变量值从服务器API获取
支持变量的自动替换
变量作用域支持多租户隔离
故障处理
DNS解析失败：记录DNS错误信息
SSL握手失败：记录SSL错误详情
HTTP重定向：支持自动跟踪
证书验证：开发环境跳过验证
响应处理：支持JSON和文本响应
认证失败：记录认证错误详情
多租户问题：记录租户ID缺失或无效的错误