# Codex 机制说明

你要的目标已单独落在：`codex/rd-team-native/`。

这套是**纯 Codex 原生**，不依赖 `python/`。

## 原语映射

| CodeBuddy 语义 | Codex 原生工具 |
|---|---|
| `team_create` | main 初始化 team registry |
| `task` | `spawn_agent`（首轮）/ `send_input`（续轮） |
| `send_message` | `send_input`（main 路由或点对点） |
| inbox 轮询 | `wait_agent` |
| `team_delete` | `close_agent` |

## 入口

- `codex/rd-team-native/rd-team/SKILL.md`
- `codex/rd-team-native/rd-team/commands/rd-team.md`
