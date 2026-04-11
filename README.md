# codex-ai-rd-team

一个以 **Python 内核（B）** 为主、并提供 **A1 兼容层（`rd-team/`）** 的 RD 多角色编排项目。

## 已实现能力

- 4 种任务模式自动判定：`new_project` / `feature` / `bugfix` / `refactor`
- 6 角色工作流编排（按模式和 `has_frontend` 生成角色链）
- AgentClient 双实现：
  - `CodexAgentClient`（真实调用 `codex exec`）
  - `EchoAgentClient`（本地回显，便于离线测试）
- Tech Profile 解析（继承、关键词匹配、配置校验）
- 运行时状态模型 + JSON 持久化
- 状态机与回退闭环：
  - reviewer `REJECT:` / tester `BUG:`/`FAIL:` 触发重试
  - 超过阈值进入 `needs_user_decision`
- 心跳/消息总线与超时重派策略
- 标准 A 文档产物落盘：
  - `docs/requirements/prd.md`
  - `docs/design/architecture.md`
  - `docs/design/api-contracts.md`
  - `docs/reviews/review-{N}.md`
- A1 兼容层目录：`rd-team/`（Skill / command / agents / shared resources）
- `/rd-team` 语义兼容：入口文档明确转调 Python CLI

## 目录概览

```text
codex-ai-rd-team/
├── config/
│   ├── role-prompts.json
│   └── tech-profiles.json
├── orchestrator/
│   ├── agent_dispatcher.py
│   ├── artifacts.py
│   ├── cli.py
│   ├── coordinator.py
│   ├── message_bus.py
│   ├── message_router.py
│   ├── mode_classifier.py
│   ├── planner.py
│   ├── profiles.py
│   ├── prompts.py
│   ├── runtime_models.py
│   ├── runtime_store.py
│   ├── state_machine.py
│   └── workflow.py
├── rd-team/
│   ├── SKILL.md
│   ├── commands/rd-team.md
│   ├── agents/*.md
│   └── shared-rd-resources/tech-profiles/tech-profiles.json
├── scripts/sync_tech_profiles.py
├── docs/
├── runtime/
└── tests/
```

## 在 Cursor 中使用（Python 内核）

```bash
python3 -m orchestrator.cli orchestrate \
  --objective "修复登录500 bug" \
  --agent-client codex \
  --runtime-dir ./runtime
```

示例输出：

```text
run_id=run-20260412013000123456 mode=bugfix profile=generic status=completed steps=4
```

### AgentClient 选择

- `--agent-client auto`（默认）：检测到 `codex` 可执行文件则用 Codex，否则回退到 Echo
- `--agent-client codex`：强制走真实 Codex 执行
- `--agent-client echo`：强制走回显执行（测试/演示）

可选参数：

```bash
--codex-bin codex
--codex-model gpt-5.4
```

### 执行契约（给 reviewer/tester 的闭环）

- `code-reviewer` 首行：`REJECT:` 或 `APPROVE:`
- `tester` 首行：`BUG:` / `FAIL:` / `PASS:`
- 其他角色首行：`DONE:`

其中 `REJECT:` / `BUG:` / `FAIL:` 会触发 coordinator 的重试/回退策略。

## A1 兼容层同步

```bash
python3 scripts/sync_tech_profiles.py
```

## 测试

```bash
python3 -m unittest discover -s tests -v
```
