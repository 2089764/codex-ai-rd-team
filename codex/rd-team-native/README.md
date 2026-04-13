# rd-team-native（你要的版本）

这是你说的目标：**不走 python 脚本，直接用 Codex 内置工具实现。**

## 怎么用

在 Codex 中加载：
- `rd-team/SKILL.md`
- `rd-team/commands/rd-team.md`
- `agents/*.md`

然后执行：
- `/rd-team <你的需求>`

或直接用脚本入口（类似 python/bin）：
- `bin/ai-rd-native`
- `bin/rd-native`
- 支持 `--objective-file` / `--dry-run` / `--verbose` / `--log-file`

最小可执行流程示例：
- `examples/index.md`（场景导航）
- `examples/minimal-runbook.md`
- `examples/new-project-runbook.md`
- `examples/feature-runbook.md`
- `examples/refactor-runbook.md`

详细场景用法（旧项目/新项目）：
- `USAGE.md`

## 核心点

- `team_create` 语义：main 初始化 registry
- `task` 语义：`spawn_agent` / `send_input`
- `send_message` 语义：`send_input`
- inbox 语义：`wait_agent`
- `team_delete` 语义：`close_agent`
- 运行治理：状态面板 + 通信日志 + 越权防护

> 这套就是纯 Codex 原生编排，不依赖 `python/`。
