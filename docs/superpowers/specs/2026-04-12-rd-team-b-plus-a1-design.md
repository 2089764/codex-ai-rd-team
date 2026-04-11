# B 主体 + A1 兼容层 设计说明

## 1. 目标

在保留现有 Python 工程（B）的前提下，完整实现 ai-rd-team 语义能力，并提供 A1 兼容层：

- 6 角色协作：analyst / architect / backend-dev / frontend-dev / code-reviewer / tester
- 4 模式编排：new_project / feature / bugfix / refactor
- 画像驱动：profile 解析 + has_frontend 决策 + role_focus 注入
- 回退闭环：review 不通过与测试失败回流开发，带轮次上限
- A1 兼容：提供 `rd-team/` 目录结构与 `/rd-team` 入口语义，实际执行转调 Python CLI

## 2. 非目标

- 不做 CodeBuddy 私有 API 的 1:1 运行时绑定（team_create/task/send_message/team_delete 原生调用）
- 不做 A2 级别的外部平台专用 adapter

## 3. 架构总览

### 3.1 分层

1. Core（orchestrator）
   - 模式判定、任务规划、调度、状态机、消息路由、落盘、prompt 渲染
2. Runtime（runtime）
   - 事件与状态快照、inbox/heartbeat 记录
3. A1 Adapter（rd-team）
   - Skill 入口与角色文档兼容，调用 Python CLI 统一执行

### 3.2 单一执行内核

所有业务流程只在 Python 内核实现一次。`rd-team/commands/rd-team.md` 仅做参数透传，不复制流程逻辑。

## 4. 模式判定设计

新增 `mode_classifier.py`：

- `bugfix`: 命中「修复/bug/报错/异常」
- `refactor`: 命中「重构/优化/改造/重写」
- `feature`: 命中「新增/加一个/扩展」
- `new_project`: 命中「做一个/创建/从零」或兜底

优先级：`bugfix > refactor > feature > new_project`。

## 5. 编排流程设计

### 5.1 new_project

analyst → architect → (backend + frontend 并行，按 has_frontend) → code-reviewer → tester

### 5.2 feature

analyst → architect → dev(s) → code-reviewer → tester

### 5.3 bugfix

dev(s) → code-reviewer → tester

### 5.4 refactor

architect → dev(s) → code-reviewer → tester

## 6. 回退与稳定性策略

- reviewer 失败：回退对应 dev，最多 2 轮
- tester 失败：回退对应 dev，最多 2 轮
- 超过轮次：状态置 `needs_user_decision`
- 心跳超时：150s 无心跳/正式消息判异常，最多重派 2 次

## 7. 消息与运行时

新增 runtime 事件流：

- `runtime/inboxes/{role}.jsonl`
- 事件类型：`heartbeat | message | result | shutdown_request`
- 协调者定时轮询（默认 30s，可配置）

## 8. 标准 A 产物

按模式生成并维护：

- `docs/requirements/prd.md`
- `docs/design/architecture.md`
- `docs/design/api-contracts.md`
- `docs/reviews/review-{N}.md`
- `runtime/run-*.json`

## 9. A1 兼容层目录

新增：

- `rd-team/SKILL.md`
- `rd-team/commands/rd-team.md`
- `rd-team/agents/{analyst,architect,backend-dev,frontend-dev,code-reviewer,tester}.md`
- `rd-team/shared-rd-resources/tech-profiles/tech-profiles.json`

并保持与 `config/tech-profiles.json` 同步（单向生成或校验脚本）。

## 10. 测试策略

1. 单元测试
   - mode 判定
   - 编排图生成
   - 回退轮次与终止条件
   - 画像解析与 has_frontend 分支
2. 集成测试
   - 4 模式端到端（mock dispatcher）
   - 心跳超时与重派
   - 产物路径与内容存在性
3. 兼容测试
   - `rd-team/` 目录完整性
   - `/rd-team` 参数转调 CLI 的行为一致性

## 11. 风险与缓解

- 风险：双层结构漂移
  - 缓解：A1 仅转调，不复制业务逻辑
- 风险：并行路径状态竞争
  - 缓解：状态机集中写入 + 原子保存
- 风险：产物模板不稳定
  - 缓解：固定模板 + golden tests

## 12. 里程碑

1. M1：模式判定 + 编排图 + 回退机制
2. M2：消息/心跳/重派 + 标准 A 产物
3. M3：A1 兼容层目录 + `/rd-team` 转调入口
4. M4：全量测试、文档与验收
