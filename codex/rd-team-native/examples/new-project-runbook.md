# rd-team-native 全流程示例（new_project 场景）

目标：从 0 到 1 跑完整链路：
`analyst -> architect -> (backend + frontend 并行) -> reviewer -> tester`

> 使用工具：`spawn_agent` / `send_input` / `wait_agent` / `close_agent`

---

## 0) 初始化 registry（main 内存）

```json
{
  "team_name": "rd-team-20260414-002",
  "mode": "new_project",
  "members": {},
  "review_round": 0,
  "test_round": 0,
  "restarts": {},
  "status": "running",
  "has_frontend": true
}
```

---

## 1) analyst 阶段

### 1.1 派发

```text
spawn_agent(agent_type="explorer", message="你是 rd-analyst。任务：输出 PRD 到 docs/requirements/prd.md；首行 DONE:；按 AC 完整拆解需求。")
```

记录 `analyst_id`。

### 1.2 轮询等待（30s）

```text
wait_agent(targets=[analyst_id], timeout_ms=30000)
```

- `HEARTBEAT:` -> 更新状态面板
- `DONE:` -> 进入用户确认

### 1.3 用户确认闸门（必须）

main 展示 PRD 摘要，用户确认后才进入 architect。

---

## 2) architect 阶段

### 2.1 派发

```text
spawn_agent(agent_type="explorer", message="你是 rd-architect。基于已确认 PRD 输出 architecture.md + api-contracts.md + docker-compose.yaml + Makefile + README；首行 DONE:。")
```

记录 `architect_id`。

### 2.2 等待

```text
wait_agent(targets=[architect_id], timeout_ms=30000)
```

`DONE:` 后检查产物完整性，再进入开发阶段。

---

## 3) 开发阶段（并行）

### 3.1 并行派发

```text
spawn_agent(agent_type="worker", message="你是 rd-backend-dev。按契约实现后端，首行 DONE:，附文件+测试结果。")
spawn_agent(agent_type="worker", message="你是 rd-frontend-dev。按契约实现前端，首行 DONE:，附文件+测试结果。")
```

记录 `backend_id`、`frontend_id`。

### 3.2 并行等待

```text
wait_agent(targets=[backend_id, frontend_id], timeout_ms=30000)
```

- 任一先完成：先记状态，不推进 reviewer
- 两者都 `DONE:`：进入 reviewer

---

## 4) reviewer 阶段

### 4.1 派发

```text
spawn_agent(agent_type="explorer", message="你是 rd-code-reviewer。只读审查；首行 APPROVE: 或 REJECT:；列阻断项。")
```

记录 `reviewer_id`。

### 4.2 等待与分支

```text
wait_agent(targets=[reviewer_id], timeout_ms=30000)
```

- `APPROVE:` -> 进入 tester
- `REJECT:` -> `review_round += 1`，回退开发：

```text
send_input(target=backend_id, message="review 退回：<问题列表>，修复后 DONE:")
send_input(target=frontend_id, message="review 退回：<问题列表>，修复后 DONE:")
```

然后回到开发并行等待；`review_round > 2` -> `needs_user_decision`。

---

## 5) tester 阶段

### 5.1 派发

```text
spawn_agent(agent_type="worker", message="你是 rd-tester。首行 PASS:/BUG:/FAIL:；BUG 必须附复现步骤。")
```

记录 `tester_id`。

### 5.2 等待与分支

```text
wait_agent(targets=[tester_id], timeout_ms=30000)
```

- `PASS:` -> 完成
- `BUG:` / `FAIL:` -> `test_round += 1`，回退开发：

```text
send_input(target=backend_id, message="tester 回退：<复现步骤+期望结果>，修复后 DONE:")
send_input(target=frontend_id, message="tester 回退：<复现步骤+期望结果>，修复后 DONE:")
```

修复后回 reviewer -> tester；`test_round > 2` -> `needs_user_decision`。

---

## 6) 超时恢复（通用）

任一角色连续约 150 秒无有效进展：

1. 抢占询问
```text
send_input(target=<id>, interrupt=true, message="请立即汇报状态（HEARTBEAT 或 DONE/APPROVE/PASS...）")
```
2. 仍无响应则重启
```text
close_agent(target=<id>)
spawn_agent(...)  # 同角色重启
```
3. 每角色最多重启 2 次，超限转 `needs_user_decision`。

---

## 7) 结束清理

```text
send_input(target=analyst_id, message="流程结束，准备关闭")
send_input(target=architect_id, message="流程结束，准备关闭")
send_input(target=backend_id, message="流程结束，准备关闭")
send_input(target=frontend_id, message="流程结束，准备关闭")
send_input(target=reviewer_id, message="流程结束，准备关闭")
send_input(target=tester_id, message="流程结束，准备关闭")

close_agent(target=analyst_id)
close_agent(target=architect_id)
close_agent(target=backend_id)
close_agent(target=frontend_id)
close_agent(target=reviewer_id)
close_agent(target=tester_id)
```

最终输出：模式、画像、回退轮次、重启次数、最终状态（completed / needs_user_decision / failed）。
