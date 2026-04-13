# rd-team-native

`rd-team-native` 是 **纯 Codex 原生编排实现**，不依赖 Python 编排器。

## 使用流程

在 Codex 中加载：
- `rd-team/SKILL.md`
- `rd-team/commands/rd-team.md`
- `agents/*.md`

然后执行：
- `/rd-team <需求描述>`

`trpc-go + vue` 场景示例：

```text
/rd-team 在现有项目中新增用户画像功能。后端使用 trpc-go，前端使用 vue，沿用当前技术栈，不切换框架或语言。
```

或直接使用脚本入口（与 `python/bin` 同级）：
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

> 该目录面向 Codex 原生工具链：`spawn_agent / send_input / wait_agent / close_agent`。
