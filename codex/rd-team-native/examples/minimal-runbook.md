# rd-team-native 最小可执行示例（Bugfix 场景）

目标：提供可直接执行的最小闭环流程。  
场景：`bugfix`（后端修复 -> 检视 -> 测试）。

> 工具：`spawn_agent` / `send_input` / `wait_agent` / `close_agent`

---

## 0. 初始化 team registry（main 内存）

```json
{
  "team_name": "rd-team-20260414-001",
  "mode": "bugfix",
  "members": {},
  "review_round": 0,
  "test_round": 0,
  "restarts": {},
  "status": "running"
}
```

---

## 1. 派发 backend-dev

```text
spawn_agent(
  agent_type="worker",
  message="你是 rd-backend-dev。任务：修复登录接口 500。输出首行必须 DONE:；附修改文件和测试命令结果。"
)
```

记录返回的 `backend_id`。

---

## 2. 等待 backend-dev（30s 轮询）

```text
wait_agent(targets=[backend_id], timeout_ms=30000)
```

处理规则：
- 收到 `HEARTBEAT:` -> 更新状态面板继续等
- 收到 `DONE:` -> 进入 reviewer
- 连续 150 秒无进展 -> 中断/重启（见第 6 节）

---

## 3. 派发 code-reviewer

```text
spawn_agent(
  agent_type="explorer",
  message="你是 rd-code-reviewer。只读审查。首行必须 APPROVE: 或 REJECT:；给出阻断项。"
)
```

记录 `reviewer_id`，然后：

```text
wait_agent(targets=[reviewer_id], timeout_ms=30000)
```

分支：
- `APPROVE:` -> 进入 tester
- `REJECT:` -> `review_round += 1`，转发修复请求给 backend-dev：

```text
send_input(target=backend_id, message="reviewer 退回：<问题列表>。请修复后回报 DONE:")
```

若 `review_round > 2`：`status=needs_user_decision`。

---

## 4. 派发 tester

```text
spawn_agent(
  agent_type="worker",
  message="你是 rd-tester。首行必须 PASS:/BUG:/FAIL:；BUG 必须附复现步骤。"
)
```

记录 `tester_id`，然后：

```text
wait_agent(targets=[tester_id], timeout_ms=30000)
```

分支：
- `PASS:` -> 完成
- `BUG:`/`FAIL:` -> `test_round += 1`，转发给 backend-dev：

```text
send_input(target=backend_id, message="tester 回退：<复现步骤+期望结果>，修复后回报 DONE:")
```

若 `test_round > 2`：`status=needs_user_decision`。

---

## 5. 路由消息模板（main 执行）

当成员输出 ROUTE 块时：

```text
send_input(target=<recipient_id>, message="[ROUTED from <sender>] <summary>\n<content>")
```

同时打印日志：

```text
ROUTED: from=<sender> to=<recipient> summary=<summary> status=sent
```

---

## 6. 超时恢复最小策略

当某角色连续约 150 秒无有效进展：

1. 尝试抢占：
```text
send_input(target=<id>, interrupt=true, message="请立即汇报当前状态，使用 HEARTBEAT: 或 DONE:/REJECT:/PASS:...")
```
2. 仍无响应：
```text
close_agent(target=<id>)
spawn_agent(...)  # 重启同角色
```
3. 每角色重启最多 2 次，超限转 `needs_user_decision`。

---

## 7. 结束清理

```text
send_input(target=backend_id, message="流程结束，准备关闭。")
send_input(target=reviewer_id, message="流程结束，准备关闭。")
send_input(target=tester_id, message="流程结束，准备关闭。")

close_agent(target=backend_id)
close_agent(target=reviewer_id)
close_agent(target=tester_id)
```

最终输出：模式、回退轮次、重启次数、结论（completed / needs_user_decision / failed）。
