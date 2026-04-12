# codex-ai-rd-team

一个以 **Python 编排内核** 为主、并提供 **A1 兼容层（`rd-team/`）** 的 RD 多角色编排项目。

## 快速上手（推荐）

建议先看：[`QUICKSTART.md`](./QUICKSTART.md)  
你日常只需要记一个入口：

```bash
./bin/ai-rd "修复登录500 bug"
```

或使用 Makefile：

```bash
make rd OBJ="修复登录500 bug"
```

## 这个项目解决什么问题

把一个自然语言目标（objective）转成可执行的多角色研发流程，并输出：

- 运行态结果：`runtime/run-<id>.json`
- 本次执行产物：`runtime/artifacts/<run_id>/...`
- 可追溯消息链与状态变化（含重试、回退、失败终止）

## 核心能力

- 4 种任务模式自动判定：`new_project` / `feature` / `bugfix` / `refactor`
- 6 角色工作流编排（按模式和 `has_frontend` 动态裁剪）
- AgentClient 双实现：
  - `CodexAgentClient`（真实调用 `codex exec`）
  - `EchoAgentClient`（本地回显，便于离线测试）
- Tech Profile 解析（继承、关键词匹配、配置校验）
- reviewer/tester 闭环：
  - `REJECT:`、`BUG:`、`FAIL:` 触发重试
  - 超过阈值进入 `needs_user_decision`
- 心跳超时重派与最终失败保护
- A1 兼容层（`rd-team/`）与 Python 内核解耦

## 目录概览

```text
codex-ai-rd-team/
├── README.md
├── QUICKSTART.md
├── ARCHITECTURE.md
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

## 文档阅读路径（按受众）

- **新同学上手**：`README.md` → `QUICKSTART.md` → `ARCHITECTURE.md`
- **内部开发/维护**：`ARCHITECTURE.md` → `docs/README.md` → `docs/design/*`
- **外部评审/展示**：`README.md` → `ARCHITECTURE.md`

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

## 运行产物位置（混合模式）

- 稳定文档（人工维护）：`docs/`
- 执行产物（自动生成）：`runtime/artifacts/<run_id>/`
- 运行态快照：`runtime/run-*.json`

## 维护命令

```bash
python3 scripts/sync_tech_profiles.py
python3 -m unittest discover -s tests -v
```
