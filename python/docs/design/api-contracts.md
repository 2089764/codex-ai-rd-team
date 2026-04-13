# API / 输出契约（稳定文档）

本文定义编排流程中的关键输入输出契约，用于降低角色协作歧义。

## 1. CLI 输入契约

核心命令：

```bash
python3 -m orchestrator.cli orchestrate --objective "<text>"
```

关键参数：

- `--objective`（必填）：任务目标
- `--profile`（可选）：显式技术画像
- `--runtime-dir`（可选）：运行态目录，默认 `./runtime`
- `--agent-client`：`auto|codex|echo`
- `--codex-bin` / `--codex-model`：Codex 后端可选项

## 2. Agent 输出首行契约

- `code-reviewer`：首行必须 `REJECT:` 或 `APPROVE:`
- `tester`：首行必须 `BUG:` / `FAIL:` / `PASS:`
- 其他角色：首行必须 `DONE:`

> 该契约直接影响 coordinator 是否触发重试或终态分流。

## 3. RuntimeState 持久化契约

`runtime/run-<id>.json` 至少包含：

- `run_id`
- `profile_name`
- `objective`
- `status`
- `queue[]`
- `messages[]`
- `shared_context`
- `step_cursor`

## 4. 执行产物契约

每次运行应在 `runtime/artifacts/<run_id>/` 下输出：

- `requirements/prd.md`（analyst）
- `design/architecture.md`（architect）
- `design/api-contracts.md`（architect）
- `reviews/review-{N}.md`（code-reviewer）

## 5. 向后兼容约束

- A1 入口 `rd-team/commands/rd-team.md` 必须持续可用
- 兼容层不应复制内核编排逻辑
