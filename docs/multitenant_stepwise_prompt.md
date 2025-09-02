# Prompt：分步骤实施 — 多租户用户管理（精简行动版）
> 目标：在现有系统上迭代实现“多租户用户管理”功能，保证租户自治、用户与租户一一映射、每租户默认 15 个用户上限、租户管理员指定与保护、强制租户范围访问。按下列步骤逐步实现并通过对应验收标准后继续下一步。

功能需求概述
1）修改Tenant模型，添加max_users字段，默认值为15
2）租户管理员（tenant_admin）能够管理本租户的用户
3）超级管理员（super_admin）在创建租户时，默认同时创建租户管理员
4）超级管理员在修改租户时能够修改租户管理员
5）租户管理员不能创建其他租户管理员
6）删除用户时进行硬删除
--
## 全局约定（在所有步骤中必须遵守）
- 每个后端接口应返回统一错误码（见末尾错误码清单）。
- 增加一个操作日志记录表，记录超级管理员
-所有对租户的操作以及用户管理的操作需要写入审计日志表 `audit_logs`：actor_user_id、actor_tenant_id（可为空）、action、target、payload、ip、timestamp。
增加一个二级菜单审计日志查询的菜单在系统管理，super_admin角色可查询到所有的审计日志，tenant_admin 只能查询到当前租户的审计日志。 
- 不得改变现有业务逻辑的数据语义；新增字段需向后兼容。
---
## 步骤 1 — 数据模型与迁移（单步事务式）
**目标**：为多租户约束和租户管理员（表与约束）。  
设计说明
在 tenants 表中增加/确认 max_users 字段，默认值为 15。
在 user_tenants 表上增加唯一约束 unique(user_id)，保证用户只能属于一个租户。
确保 role 字段包含 tenant_admin、user 两个值。
应用层增加逻辑：禁止删除最后一个 tenant_admin。
修改点清单
数据库迁移脚本：增加 max_users 字段，默认值 15。
增加 unique(user_id) 约束。
增加 CHECK(max_users >= 1) 约束。
确认并补充索引：users.username，tenants.name，user_tenants(tenant_id)。
验收标准
tenants.max_users 正常存储。
每个用户仅能属于一个租户。
删除/降级用户时，保证租户始终至少有一个管理员。
---
## 步骤 2 — 后端：租户管理 API（system_admin 权限）
**目标**：平台管理员能管理租户并在创建时指定初始租户管理员（首位管理员）。  
**后端任务**（接口契约 & 逻辑）：
1. `POST /api/v1/tenants` — 创建租户  
   - 请求必填：`name`, 可选：`max_users`, 可选：`admin`（{username,password}）用于同时创建首个 tenant_admin。  
   - 事务性操作：创建 tenant -> 若提供 admin，创建 user 并写入 `user_tenant_map` 角色为 `tenant_admin`。  
   - 校验：`name` 唯一、`max_users` >= 1。  
2. `GET /api/v1/tenants` — 列表（分页、包含 current_user_count）  
3. `PUT /api/v1/tenants/{tid}` — 修改（name/max_users/status）  
   - 校验：若设置 `max_users < current_user_count` 则拒绝（返回 `INVALID_MAX_USERS`）。  
4. `DELETE /api/v1/tenants/{tid}` — 删除租户（需二次确认，级联或软删用户及业务数据=）  
**事务与错误处理**：
- 创建租户 + 初始管理员必须在一个事务内完成或回滚。  
**验收**：
- API 能创建租户并可选创建首位管理员；若 admin 提供且 username 冲突，创建失败并回滚。  
- `max_users` 小于现有用户数时拒绝。
---
## 步骤 3 — 后端：用户管理 API（tenant_admin 权限，限定本租户）
**目标**：租户管理员能在本租户内增删改用户，受 max_users 限制并不能删除自身/最后一个 admin。  
**后端任务**（接口契约 & 逻辑）：
1. `POST /api/v1/tenants/{tid}/users` — 创建用户  
   - 请求必填：`username`, `password`, `role`（tenant_admin/user）, `status`。  
   - 校验序列：  
     a) 请求者必须为 `system_admin` 或该 `tenant` 的 `tenant_admin`。  
     b) `tid` 必须等于请求者 token 中的 `tenant_id`（除 system_admin）。  
     c) 当前 `user_count < tenants.max_users`，否则返回 `USER_LIMIT_REACHED`。  
     d) `username` 全局唯一。  
   - 操作：创建 `users`，写 `user_tenant_map(user_id, tid, role)`。  
2. `GET /api/v1/tenants/{tid}/users` — 列表（分页）  
3. `PUT /api/v1/tenants/{tid}/users/{uid}` — 修改用户（username, role, status）  
   - 禁止：租户管理员将自己降级或删除自己（返回 `FORBIDDEN_SELF_DESTRUCT`）。  
   - 禁止：若降级/删除会导致该租户没有任何 `tenant_admin`，返回 `TENANT_ADMIN_REQUIRED`。  
4. `DELETE /api/v1/tenants/{tid}/users/{uid}` — 删除用户（含校验同上）  
5. `POST /api/v1/tenants/{tid}/users/{uid}/reset-password` — 重置密码（返回操作日志）  
**验收**：
- 用户创建时会校验并拒绝超过 `max_users`。  
- 禁止删除最后一个 `tenant_admin` 或删除自身。  
- 所有用户 CRUD 均写入 `audit_logs`。
---
## 步骤 4 — 后端：认证与租户约束中间件（核心安全）
**目标**：确保所有业务 API 自动按 `tenant_id` 作用域过滤；登录返回租户信息到 token。  
**后端任务**：
1. 登录流程：在 `POST /api/v1/auth/login` 返回 JWT，Claims 包含 `user_id`, `tenant_id`, `role`。若用户不存在或用户/租户为 disabled，返回 `USER_DISABLED` / `TENANT_DISABLED`。  
2. 增加全局中间件（或 ORM 拦截器）：  
   - 解码 JWT，取 `tenant_id`。  
   - 对所有业务查询/写入在入口层追加 `WHERE tenant_id = <claims.tenant_id>`（system_admin 可跳过但不能访问业务数据）。  
   - 如果请求路径是 tenant 管理且调用者 role=system_admin，则允许访问。  
3. 所有 controller 层必须校验 `tenant_id` 与传入的 `tid` 匹配（防止 URL 掺入其他 tid）。  
**验收**：
- 采用 Postman/集成测试验证：用户 A（tenant 1）无法访问 tenant 2 的用户数据（返回 `FORBIDDEN_CROSS_TENANT`）。
---
## 步骤 5 — 前端：页面与控件（分离实现）
**目标**：在前端新增/修改界面并做本地校验，避免无效请求。  
**前端任务**（每个页面需列出最小字段与校验）：
A. **租户管理（超级管理员）**：
- 列表页：显示 `name`, `status`, `max_users`, `current_user_count`，支持搜索/分页。  
- 新建弹窗：`name`（非空）、`max_users`（整数≥1）、可输入初始 admin（username,password）可选。  
- 编辑：修改 `name/max_users/status`（对 `max_users` 做前端提示避免违规值）。
B. **租户用户管理（tenant_admin 租户管理员）**：
-  只能 tenant_admin 角色能访问 
- 列表页：`username`, `role`, `status`, `last_login`，支持搜索/分页。  
- 新建表单：`username`（非空）、`password`（符合密码策略）、`role`、`status`。  
- 删除操作：二次确认；若尝试删除自己，前端禁止并提示。  
- 重置密码：弹窗或自动生成并显示一次（仅显示一次）。
C. **登录页**：
- 登录成功后本地存储 JWT（HttpOnly cookie 推荐 or localStorage），并展示 `tenant` 名称与角色在 header。  
**前端验收**：
- 所有表单前端校验通过后才发请求；后端错误（如 USER_LIMIT_REACHED）要能在 UI 上友好显示并指向操作建议。
---
需要修改前端的dashboard 页面,增加租户用户的统计数据展示， 其中超级管理员dashboard统计所有的租户的用户使用情况，租户管理员的 dashboard 只统计本租户，统计样式保持一致
## 步骤 7 — 自动化测试清单（必须）
两个不同的租户的用户 一个是 ceshi1 密码是 123456 ，一个是 ceshi2 密码是 123456 ，超级用户是 superadmin 密码是 1Q2W3E， 前端端口是8080，后端服务是 5001
为每个 API 编写单元与集成测试，至少包含：
1. 登录成功/失败/租户禁用/用户禁用用例。  
2. 创建租户（含 admin），校验事务回滚（admin username 冲突）。  
3. 创建用户达到 `max_users` 的边界测试（=max & =max+1）。  
4. 尝试跨租户读写（应被拒绝）。  
5. 删除/降级最后一个 admin（应被拒绝）。  
Tenant Admin只能管理所属租户的用户
普通用户无法访问管理功能
Tenant Admin不能创建其他Tenant Admin
6. audit_logs 记录检查（每次增删改应生成日志）。  
------
## 步骤 9 — 验收条件（最终交付前必须全部通过）
- 所有步骤对应的单元/集成/端到端测试通过（CI）。  
- 无跨租户数据访问漏洞（渗透/安全扫描）。  
- 前端表单校验与后端校验一致。  
---
## 常用错误码（返回统一结构 `{code, message, details?}`）
- `INVALID_INPUT` — 参数校验失败  
- `TENANT_NAME_EXISTS` — 创建租户名已存在  
- `INVALID_MAX_USERS` — 不合法的 max_users（小于已存在用户数或 <1）  
- `USER_LIMIT_REACHED` — 本租户用户数已达上限  
- `USERNAME_EXISTS` — 用户名已存在  
- `INVALID_CREDENTIALS` — 登录失败  
- `USER_DISABLED` — 用户被禁用  
- `TENANT_DISABLED` — 租户被禁用  
- `FORBIDDEN_CROSS_TENANT` — 跨租户访问被禁止  
- `TENANT_ADMIN_REQUIRED` — 操作会导致租户无管理员，禁止  
- `FORBIDDEN_SELF_DESTRUCT` — 禁止删除/降级自己
---
## 交付清单（每步完成后提交）
1. 数据迁移脚本 + 回滚脚本。  
2. 后端 API 实现 + OpenAPI 文档（包含 request/response/errorcodes）。  
3. 中间件/拦截器实现（租户强制过滤）。  
4. 前端页面/表单实现 + 校验逻辑。  
5. 完整自动化测试套件（单元/集成/端到端）。  