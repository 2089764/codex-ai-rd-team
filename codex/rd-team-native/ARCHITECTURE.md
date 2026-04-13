# rd-team-native 架构说明（Codex 原生编排）

本文描述 `codex/rd-team-native`：
**不依赖 Python 编排脚本**，直接使用 Codex 原生工具编排 6 角色研发团队。

---

## 原语映射

| CodeBuddy 语义 | Codex 原生工具 |
|---|---|
| `team_create` | main 初始化 team registry（内存） |
| `task` | `spawn_agent`（首次派发）/ `send_input`（续轮） |
| `send_message` | `send_input`（main 路由转发） |
| inbox 轮询 | `wait_agent(timeout_ms=30000)` |
| `team_delete` | `close_agent`（全量清理） |

---

## 设计目标

- 真多 Agent：analyst / architect / backend-dev / frontend-dev / code-reviewer / tester
- 4 模式编排：new_project / feature / bugfix / refactor
- reviewer/tester 自主回退闭环（最多 2 轮）
- 心跳、超时、重启机制（30s 轮询、150s 超时、最多重启 2 次）
- 技术画像驱动（读取 `tech-profiles.json`）

---

## 角色与职责边界

- `rd-analyst`：PRD 与验收标准
- `rd-architect`：架构与接口契约、任务拆解、环境规划
- `rd-backend-dev`：后端实现与测试
- `rd-frontend-dev`：前端实现与测试（仅 `has_frontend=true`）
- `rd-code-reviewer`：只读审查，输出 `APPROVE/REJECT`
- `rd-tester`：测试执行，输出 `PASS/BUG/FAIL`

> 约束：协调者只编排不代写业务代码。

---

## 通信拓扑（逻辑直连，物理经 main 路由）

```text
analyst <-> architect
backend-dev <-> frontend-dev
code-reviewer <-> dev(s)
tester <-> dev(s)/analyst
        \    |
           main
```

实现方式：成员产生“路由请求”，由 main 用 `send_input` 转发给目标 Agent。

---

## 模式流程

- new_project: analyst → architect → 并行(backend + frontend) → reviewer → tester
- feature: analyst → architect → dev(s) → reviewer → tester
- bugfix: dev(s) → reviewer → tester
- refactor: architect → dev(s) → reviewer → tester

关键闸门：
- analyst 完成 PRD 后必须经过用户确认，才进入 architect
- reviewer / tester 回退最多 2 轮，超限转 `needs_user_decision`

---

## 运行时控制

- 轮询：每 30 秒 `wait_agent`
- 超时：连续 150 秒无有效进展 -> `send_input(interrupt=true)` 尝试抢占
- 失败恢复：仍无进展则 `close_agent + spawn_agent` 重启同角色
- 重启上限：每角色最多 2 次

---

## 与 CodeBuddy 的差异及等价策略

- CodeBuddy 的 `.codebuddy/agents` 注册机制
- CodeBuddy 的 frontmatter `tools` 平台硬白名单

等价补偿机制：角色提示词强约束 + main 编排审计 + 输出契约前缀。
