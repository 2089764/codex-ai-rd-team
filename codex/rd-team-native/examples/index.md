# Runbook 导航（rd-team-native）

请按当前任务场景选择：

## 1) 修复 Bug（最小闭环）
- 文件：`minimal-runbook.md`
- 流程：`backend-dev -> reviewer -> tester`
- 适用：线上报错、接口异常、回归修复

## 2) 新建项目（全流程）
- 文件：`new-project-runbook.md`
- 流程：`analyst -> architect -> 并行开发 -> reviewer -> tester`
- 适用：从 0 到 1

## 3) 新增功能（增量变更）
- 文件：`feature-runbook.md`
- 流程：`analyst -> architect -> dev(s) -> reviewer -> tester`
- 适用：已有项目加功能

## 4) 代码重构（结构优化）
- 文件：`refactor-runbook.md`
- 流程：`architect -> dev(s) -> reviewer -> tester`
- 适用：性能优化、分层治理、技术债清理

---

## 通用执行要点

- 工具固定：`spawn_agent / send_input / wait_agent / close_agent`
- 轮询：每 30 秒 `wait_agent(timeout_ms=30000)`
- 超时：150 秒无进展触发恢复（最多重启 2 次）
- 回退：review/test 最多 2 轮，超限转 `needs_user_decision`
- 协调者只编排，不写业务代码

---

## 推荐使用顺序

1. 先看对应 runbook（上面 4 选 1）
2. 再看：`../rd-team/commands/rd-team.md`（统一编排规则）
3. 最后看：`../agents/*.md`（角色边界与输出契约）
