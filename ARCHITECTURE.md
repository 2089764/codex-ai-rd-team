# Architecture

## 总体设计

项目采用 **B 主体 + A1 兼容层**：

1. **B（Python 内核）**：所有业务逻辑唯一实现于 `orchestrator/`
2. **A1（兼容层）**：`rd-team/` 仅提供 Skill/命令/角色文档与资源目录，不重复实现编排逻辑

核心原则：**单一执行内核，避免双实现漂移**。

## 核心模块

### 1) 配置与画像

- `config/tech-profiles.json`：技术画像配置
- `orchestrator/profiles.py`：加载、校验、继承解析、关键词匹配

### 2) 模式与工作流

- `orchestrator/mode_classifier.py`：4 模式判定
- `orchestrator/workflow.py`：按模式 + `has_frontend` 构建角色链
- `orchestrator/planner.py`：基于 profile 生成工作项

### 3) 运行时与状态控制

- `orchestrator/runtime_models.py`：`RuntimeState`/`WorkItem`/`RoutedMessage`
- `orchestrator/state_machine.py`：状态迁移约束
- `orchestrator/runtime_store.py`：运行态持久化

### 4) 调度与通信

- `orchestrator/agent_clients.py`：AgentClient 实现（Codex / Echo）
- `orchestrator/agent_dispatcher.py`：统一 dispatch 抽象
- `orchestrator/message_bus.py`：心跳/消息事件总线
- `orchestrator/coordinator.py`：主循环（调度、重试、回退、超时重派、落盘）

### 5) 产物与提示词

- `orchestrator/artifacts.py`：标准 A 文档产物写入
- `config/role-prompts.json` + `orchestrator/prompts.py`：角色提示词模板

### 6) CLI 入口

- `orchestrator/cli.py`
  - 解析目标
  - 选择 AgentClient（`auto/codex/echo`）
  - 判定 mode
  - 应用 mode-aware flow
  - 驱动 coordinator

## 回退与恢复策略

- Reviewer/Tester 反馈回路：
  - `CodexAgentClient` 为 reviewer/tester 注入输出前缀契约
  - `REJECT:` / `BUG:` / `FAIL:` 触发重试
  - 超过阈值进入 `needs_user_decision`
- 心跳超时重派：
  - 超时触发重派计数
  - 超上限置 `FAILED`

## 产物边界

- 运行时状态：`runtime/run-*.json`
- 标准 A 文档：
  - `docs/requirements/prd.md`
  - `docs/design/architecture.md`
  - `docs/design/api-contracts.md`
  - `docs/reviews/review-{N}.md`

## A1 兼容层边界

`rd-team/` 负责兼容目录与入口语义；`rd-team/commands/rd-team.md` 明确转调：

```bash
python -m orchestrator.cli orchestrate --objective "<用户输入>"
```

不在兼容层重复实现编排算法。
