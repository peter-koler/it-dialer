# IT-Dialer 网络拨测系统

IT-Dialer 是一个网络拨测系统，用于监控网络连接状态和性能。该系统支持创建多种类型的拨测任务（如ping），并提供实时监控和历史数据分析功能。

## 功能特性

### 1. 拨测任务管理
- 创建、编辑、删除拨测任务
- 支持多种拨测类型（目前支持ping）
- 可配置目标地址、执行间隔等参数
- 任务状态管理（启用/禁用）

### 2. 实时监控与数据收集
- Agent自动执行拨测任务
- 实时收集网络延迟、丢包率等指标
- 数据自动上报到后端服务器

### 3. 数据展示与分析
- 实时查看任务执行结果
- 历史数据查询与分析
- 图表化展示网络性能趋势

### 4. 节点管理
- Agent自动注册和心跳上报
- 节点状态自动管理（运行中、超时、下线）
- 前端可视化节点管理界面
- 支持节点手动上下线和删除操作

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
- SQLite 数据库（开发环境）
- SQLAlchemy ORM
- Alembic 数据库迁移工具

### 前端
- Vue 3 + Vite
- Ant Design Vue 4.x
- Pinia (状态管理)
- Vue Router 4

### 数据库
- SQLite (开发环境)
- MySQL 8.x (生产环境)

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
- `GET /api/v1/tasks` - 获取任务列表
- `POST /api/v1/tasks` - 创建任务
- `PUT /api/v1/tasks/<id>` - 更新任务
- `DELETE /api/v1/tasks/<id>` - 删除任务

### 结果管理
- `GET /api/v1/results` - 获取结果列表
- `POST /api/v1/results` - 上报结果

### 节点管理
- `GET /api/v1/nodes` - 获取节点列表
- `POST /api/v1/nodes/register` - 注册节点
- `POST /api/v1/nodes/heartbeat` - 节点心跳
- `PUT /api/v1/nodes/status` - 更新节点状态
- `DELETE /api/v1/nodes/<id>` - 删除节点

## 拨测Agent

### 功能概述

拨测Agent是一个独立的Python程序，支持插件化扩展，能够执行各种网络拨测任务并将结果上报给主系统。

### 模块结构

1. **Agent主模块** (`agent/agent.py`)
   - 支持插件动态加载
   - 从配置中获取拨测任务
   - 执行拨测任务并上报结果

2. **插件模块** (`agent/plugins/`)
   - 实现具体的拨测任务
   - 当前包含ping插件

3. **任务配置模块** (`agent/config/tasks.py`)
   - 提供拨测任务的配置管理
   - 存储和管理拨测任务的配置信息

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

## 许可证

MIT License

## API文档

启动后端服务后，访问 `http://localhost:5000/docs/` 查看API文档。

我已经完成了对任务详情页面的修改，主要做了以下几项工作：

1. 创建了中文地区名称映射文件
创建了一个新的文件 /Users/peter/Documents/code/boce/it-dialer/frontend/src/utils/regionNames.js，其中包含了中国各省市地区的行政区划代码到中文名称的映射。这个文件涵盖了从直辖市到各省、市、自治区、特别行政区的完整映射。

2. 修改了任务详情页面
对 /Users/peter/Documents/code/boce/it-dialer/frontend/src/views/TaskDetail.vue 文件进行了以下修改：

添加了从路由中获取任务ID的功能
修改了 fetchProbeData 方法，使用真实的API接口获取数据，而不是模拟数据
添加了将 agent_area 字段从拼音转换为中文地区名称的功能
使用新创建的 regionNames 映射来显示中文地区名称
现在，当用户查看任务详情时，页面将：

从API获取真实的拨测点数据
将 agent_area 字段（如 "guangzhou"）转换为中文地区名称（如 "广州市"）
正确显示分页数据和总记录数
3. 具体实现细节
使用 useRoute() 获取当前任务的ID
通过 /api/v1/results?task_id=${taskId} 接口获取真实的拨测结果数据
使用新创建的 regionNames 工具将拼音地区代码转换为中文名称
保留了原有的分页功能和数据处理逻辑

拆分后的组件结构
TaskDetail.vue - 主组件，负责整体协调和数据管理
SearchBar.vue - 搜索栏组件
StatusTag.vue - 状态标签组件
TaskDetailModal.vue - 任务详情模态框组件
ProbeList.vue - 拨测点列表组件
TaskCharts.vue - 任务图表展示组件
ProbeDetailModal.vue - 拨测点详情模态框组件
ProbeHistoryTable.vue - 拨测点历史记录表格组件
主要改进点
职责分离：每个组件都有明确的职责，便于维护和扩展
代码复用：如 StatusTag 组件可以在多处复用
可维护性：每个文件都控制在300行以内，便于阅读和修改
可测试性：小而专注的组件更容易进行单元测试
组件关系
TaskDetail.vue (主组件)
├── SearchBar.vue (搜索栏)
├── TaskDetailModal.vue (任务详情模态框)
│   ├── StatusTag.vue (状态标签)
│   ├── ProbeList.vue (拨测点列表)
│   │   └── StatusTag.vue
│   └── TaskCharts.vue (任务图表)
└── ProbeDetailModal.vue (拨测点详情模态框)
    ├── StatusTag.vue
    └── ProbeHistoryTable.vue (历史记录表格)
        └── StatusTag.vue

        
如果有API ，请把API 的路径配置单独放在 API 的目录下，避免进行在页面上进行直接调用




创建了新的目录结构：



全国拨测点分布图  没有正常显示，下面是我提供给你的信息
/src/components/EnhancedChinaMap/ - 存放所有相关文件
EnhancedChinaMap.vue - 主组件文件
mapUtils.js - 地图数据处理逻辑
mapStyling.js - 地图样式处理逻辑
mapInteractions.js - 地图交互处理逻辑
各文件功能说明：
EnhancedChinaMap.vue - 主组件，负责模板和生命周期管理
mapUtils.js - 包含地图数据加载、编码转换等工具函数
mapStyling.js - 包含地图样式处理、颜色计算、交互效果等
mapInteractions.js - 包含地图交互逻辑，如下钻、返回等
