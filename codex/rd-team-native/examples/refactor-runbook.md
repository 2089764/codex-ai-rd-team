# rd-team-native 重构示例（refactor 场景）

目标：对现有模块做结构性优化，完整走通：
`architect -> dev(s) -> reviewer -> tester`

> 工具：`spawn_agent` / `send_input` / `wait_agent` / `close_agent`

---

## 0) 初始化 registry（main 内存）

```json
{
  "team_name": "rd-team-20260414-004",
  "mode": "refactor",
  "members": {},
  "review_round": 0,
  "test_round": 0,
  "restarts": {},
  "status": "running",
  "has_frontend": "按画像解析结果"
}
```

说明：refactor 默认从 `architect` 开始，先定重构边界再进入实现。

---

## 1) architect（重构设计）

### 1.1 派发

```text
spawn_agent(
  agent_type="explorer",
  message="你是 rd-architect。任务：制定重构方案（边界/迁移步骤/兼容策略/回滚方案）；首行 DONE:。"
)
```

记录 `architect_id`。

### 1.2 等待

```text
wait_agent(targets=[architect_id], timeout_ms=30000)
```

`DONE:` 后检查是否包含：
- 重构目标与非目标
- 迁移分步计划
- 兼容策略
- 回滚方案

如涉及对外行为变化，main 需先请求用户确认。

---

## 2) dev 实现（按 has_frontend 决定并行）

### 2.1 派发

后端：

```text
spawn_agent(
  agent_type="worker",
  message="你是 rd-backend-dev。按重构方案实施；保持外部契约稳定；首行 DONE:；附文件+测试结果。"
)
```

前端（若 has_frontend=true）：

```text
spawn_agent(
  agent_type="worker",
  message="你是 rd-frontend-dev。按重构方案实施前端层重构；保持用户可见行为一致；首行 DONE:。"
)
```

记录 `backend_id` / `frontend_id`。

### 2.2 等待

```text
wait_agent(targets=[backend_id, frontend_id], timeout_ms=30000)
```

- 后端必需 `DONE:`
- 有前端时需并行全部 `DONE:` 才进 reviewer

---

## 3) reviewer（重构风险审查）

### 3.1 派发

```text
spawn_agent(
  agent_type="explorer",
  message="你是 rd-code-reviewer。审查重构后的一致性/安全性/回归风险；首行 APPROVE: 或 REJECT:。"
)
```

记录 `reviewer_id`。

### 3.2 等待与分支

```text
wait_agent(targets=[reviewer_id], timeout_ms=30000)
```

- `APPROVE:` -> 进入 tester
- `REJECT:` -> `review_round += 1`，回退开发：

```text
send_input(target=backend_id, message="review 退回：<阻断项>，修复后 DONE:")
# 有 frontend 时同样回退 frontend_id
```

`review_round > 2` -> `needs_user_decision`。

---

## 4) tester（回归验证）

### 4.1 派发

```text
spawn_agent(
  agent_type="worker",
  message="你是 rd-tester。重点做回归测试与边界测试；首行 PASS:/BUG:/FAIL:；BUG 必须可复现。"
)
```

记录 `tester_id`。

### 4.2 等待与分支

```text
wait_agent(targets=[tester_id], timeout_ms=30000)
```

- `PASS:` -> 完成
- `BUG:` / `FAIL:` -> `test_round += 1`，回退开发：

```text
send_input(target=backend_id, message="tester 回退：<复现步骤+期望结果>，修复后 DONE:")
# 有 frontend 时同样回退 frontend_id
```

`test_round > 2` -> `needs_user_decision`。

---

## 5) refactor 场景专属检查点

进入测试前，main 需确认：

1. 外部接口是否保持兼容
2. 关键链路是否有回归测试
3. 重构是否控制在既定边界（无无关扩散）
4. 回滚路径是否清晰可执行

---

## 6) 超时恢复（通用）

连续约 150 秒无有效进展：

1. 抢占：
```text
send_input(target=<id>, interrupt=true, message="请立即回报状态（HEARTBEAT 或 DONE/APPROVE/PASS...）")
```
2. 仍无响应：
```text
close_agent(target=<id>)
spawn_agent(...)  # 同角色重启
```
3. 每角色最多重启 2 次，超限转 `needs_user_decision`。

---

## 7) 结束清理

```text
send_input(target=architect_id, message="流程结束，准备关闭")
send_input(target=backend_id, message="流程结束，准备关闭")
# 如有 frontend
send_input(target=frontend_id, message="流程结束，准备关闭")
send_input(target=reviewer_id, message="流程结束，准备关闭")
send_input(target=tester_id, message="流程结束，准备关闭")

close_agent(target=architect_id)
close_agent(target=backend_id)
# 如有 frontend
close_agent(target=frontend_id)
close_agent(target=reviewer_id)
close_agent(target=tester_id)
```

最终输出：
- 模式：refactor
- 画像：effective_profile
- has_frontend
- 回退轮次（review/test）
- 重启次数
- 结论（completed / needs_user_decision / failed）
