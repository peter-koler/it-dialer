# IT-Dialer 网络拨测系统

IT-Dialer 是一个网络拨测系统，用于监控网络连接状态和性能。该系统支持创建多种类型的拨测任务（如ping），并提供实时监控和历史数据分析功能.

**版本**: 1.0.0

## 功能特性

### 1. 拨测任务管理
- 创建、编辑、删除拨测任务
- 支持多种拨测类型（ping、TCP、HTTP、API多步骤事务）
- 可配置目标地址、执行间隔、认证信息等参数
- 支持系统变量引用（$public_开头）
- 支持任务状态管理（启用/禁用）
- 支持多节点执行（agent_ids配置）

### 2. 实时监控与数据收集
- Agent自动执行拨测任务
- 实时收集网络延迟、丢包率、响应时间等指标
- 支持DNS解析时间、TCP连接时间、SSL握手时间等高级指标
- 数据自动上报到后端服务器
- 支持历史数据查询和分析
- 支持响应时间趋势图

### 3. 数据展示与分析
- 实时查看任务执行结果
- 历史数据查询与分析
- 图表化展示网络性能趋势
- 支持多维度筛选（时间范围、任务类型、执行状态）
- 支持告警规则配置
- 支持告警历史查询

### 4. 节点管理
- Agent自动注册和心跳上报
- 节点状态自动管理（运行中、超时、下线）
- 支持节点手动上下线和删除操作
- 支持区域划分（agent_area配置）

### 5. 系统变量管理
- 支持创建、编辑、删除系统变量
- 支持变量加密存储（is_secret标记）
- 支持变量作用域管理
- 支持在任务配置中引用系统变量

### 6. API拨测增强
- 支持多步骤API事务测试
- 支持变量提取（JSONPath、正则表达式）
- 支持断言验证（状态码、响应时间、响应内容）
- 支持多种HTTP方法（GET、POST等）
- 支持认证配置（OAuth1、OAuth2、Bearer Token）
- 支持断言触发告警

## 系统架构

```
┌─────────────┐    HTTP API    ┌──────────────┐    数据存储    ┌─────────────┐
│   前端界面   │ ◄─────────────► │   后端服务    │ ◄─────────────► │   数据库     │
└─────────────┘               └──────────────┘               └─────────────┘
                                      │
                                      │ 监控任务
                              ┌───────▼───────┐
                              │   Agent节点   │
                              └───────────────┘
```

## 技术栈

### 后端
- Python 3.8+
- Flask Web框架
- SQLAlchemy ORM
- Alembic 数据库迁移工具
- JWT 认证
- APScheduler 定时任务
- SQLite 数据库（开发环境）
- MySQL 8.x（生产环境）
- Docker 容器化部署

### 前端
- Vue 3 + Vite
- Ant Design Vue 4.x
- Pinia (状态管理)
- Vue Router 4
- ECharts 数据可视化
- Leaflet 地图库
- AntV/G2Plot 图表库

## 安装与部署

### 环境要求
- Python 3.8+
- Node.js 14+
- npm 6+

### 后端服务部署

1. 进入后端目录
```bash
cd backend
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 初始化数据库
```bash
python init_db.py
```

4. 启动服务
```bash
python run.py
```

### 前端部署

1. 进入前端目录
```bash
cd frontend
```

2. 安装依赖
```bash
npm install
```

3. 启动开发服务器
```bash
npm run dev
```

### Agent部署

1. 进入Agent目录
```bash
cd agent
```

2. 根据需要修改配置文件 `agent_config.json`

3. 启动Agent
```bash
python agent.py
```

## 配置说明

### Agent配置 (agent_config.json)
```json
{
  "agent_id": "default_agent",      // Agent唯一标识
  "server_url": "http://localhost:5000",  // 后端服务地址
  "plugins_dir": "plugins",        // 插件目录
  "report_interval": 60,           // 上报间隔（秒）
  "log_level": "INFO",             // 日志级别
  "agent_area": "default_area"     // Agent区域
}
```

## API接口

### 任务管理
- `GET /api/v1/tasks` - 获取任务列表（支持类型、状态、关键词筛选）
- `POST /api/v1/tasks` - 创建任务（支持多步骤API配置）
- `PUT /api/v1/tasks/<id>` - 更新任务（支持启用/禁用、间隔修改）
- `GET /api/v1/tasks/<id>` - 获取任务详情
- `DELETE /api/v1/tasks/<id>` - 删除任务

### 结果管理
- `GET /api/v1/results` - 获取结果列表（支持时间范围、任务ID筛选）
- `POST /api/v1/results` - 上报结果（支持agent_id和agent_area）
- `GET /api/v1/results/<int:result_id>` - 获取结果详情

### 节点管理
- `GET /api/v1/nodes` - 获取节点列表（支持状态、关键词筛选）
- `POST /api/v1/nodes/register` - 注册节点
- `POST /api/v1/nodes/heartbeat` - 节点心跳
- `PUT /api/v1/nodes/status` - 更新节点状态
- `DELETE /api/v1/nodes/<id>` - 删除节点
- `POST /api/v1/nodes/timeout-check` - 检查超时节点

### 系统变量管理
- `GET /api/v1/system-variables` - 获取系统变量列表（支持分页、关键词搜索）
- `POST /api/v1/system-variables` - 创建系统变量（$public_格式）
- `GET /api/v1/system-variables/<id>` - 获取变量详情
- `PUT /api/v1/system-variables/<id>` - 更新系统变量
- `DELETE /api/v1/system-variables/<id>` - 删除系统变量

### 告警管理
- `GET /api/v1/alerts` - 获取告警列表（支持任务ID、时间范围筛选）
- `GET /api/v1/alerts/<id>` - 获取告警详情
- `POST /api/v1/alerts` - 创建告警规则
- `PUT /api/v1/alerts/<id>` - 更新告警规则
- `DELETE /api/v1/alerts/<id>` - 删除告警规则

## 拨测Agent

### 功能概述
拨测Agent是一个独立的Python程序，支持插件化扩展，能够执行各种网络拨测任务并将结果上报给主系统。新增功能包括：
- 支持多步骤API事务测试
- 支持变量提取（JSONPath、正则表达式）
- 支持断言验证（状态码、响应时间、响应内容）
- 支持多种HTTP方法和认证方式（OAuth1、OAuth2、Bearer Token）
- 支持断言触发告警
- 支持DNS解析时间、TCP连接时间、SSL握手时间等高级指标

### 模块结构

1. **Agent主模块** (`agent/agent.py`)
   - 支持插件动态加载
   - 从服务器获取系统变量（$public_开头）
   - 支持任务执行结果上报
   - 支持SSL证书验证跳过
   - 支持变量嵌套替换

2. **插件模块** (`agent/plugins/`)
   - `api.py`: 支持多步骤API测试、变量提取、断言验证
   - `http_plugin.py`: 支持DNS解析时间、连接时间、SSL握手时间、首字节时间、下载时间等指标
   - `ping.py`: 支持ICMP协议测试
   - `tcp.py`: 支持TCP端口连接测试

3. **任务配置模块** (`agent/config/tasks.py`)
   - 提供拨测任务的配置管理
   - 存储和管理拨测任务的配置信息
   - 支持V2格式的initialVariables配置

4. **任务管理模块** (`agent/management/tasks.py`)
   - 展示Agent执行的拨测数据
   - 存储和查询任务执行结果

### 插件开发

插件需要实现以下接口：

```python
# 插件名称（必须）
PLUGIN_NAME = "plugin_name"

def execute(task):
    """
    执行任务
    :param task: 任务配置
    :return: 执行结果
    """
    pass
```

### 运行Agent

```bash
cd agent
python agent.py
```

## Docker部署

系统支持Docker部署，使用docker-compose可以一键启动所有服务：

```bash
docker-compose up -d
```

## 项目特色

- **多协议支持**：支持ping、TCP、HTTP、API等多类型拨测
- **可视化增强**：支持响应时间趋势图、丢包率分析、地图可视化
- **地域分析**：支持按省份/城市进行数据聚合分析
- **交互优化**：响应式设计适配不同屏幕尺寸
- **数据聚合**：支持按时间和地域维度聚合分析
- **时间分析**：支持自定义时间范围筛选和快捷时间选择
- **任务调试**：支持API任务调试模式和历史回溯
- **变量系统**：支持系统变量加密存储和作用域管理
- **断言验证**：支持API任务断言验证
- **多级地图**：支持中国省市县三级地图下钻
- **连接分析**：支持TCP连接时间分解
- **事务跟踪**：支持多步骤API事务跟踪
- **变量跟踪**：支持API任务变量作用域跟踪
- **告警系统**：支持多级别告警配置和历史分析
- **扩展性**：插件化架构支持快速扩展新类型拨测
- **安全性**：系统变量加密存储、JWT认证、HTTPS支持

## 许可证

MIT License

## API文档

- **API断言验证**：支持JSONPath、正则表达式等提取方式（参见[帮助手册.txt](file:///Users/peter/Documents/code/boce/it-dialer/帮助手册.txt））
- **地图工具**：
  - `mapUtils.js`: 地图数据加载、编码转换等工具函数
  - `mapStyling.js`: 地图样式处理、颜色计算、交互效果
  - `mapInteractions.js`: 地图交互逻辑（下钻、返回等）
