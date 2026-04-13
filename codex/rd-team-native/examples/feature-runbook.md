# rd-team-native 增量功能示例（feature 场景）

目标：在已有项目上新增功能，完整走通：
`analyst -> architect -> dev(s) -> reviewer -> tester`

> 工具：`spawn_agent` / `send_input` / `wait_agent` / `close_agent`

---

## 0) 初始化 registry（main 内存）

```json
{
  "team_name": "rd-team-20260414-003",
  "mode": "feature",
  "members": {},
  "review_round": 0,
  "test_round": 0,
  "restarts": {},
  "status": "running",
  "has_frontend": "按画像解析结果"
}
```

说明：feature 与 new_project 的核心差异是**不从零初始化工程**，只做增量变更。

---

## 1) analyst（需求增量定义）

### 1.1 派发

```text
spawn_agent(
  agent_type="explorer",
  message="你是 rd-analyst。任务：针对已有项目新增功能，输出增量 PRD（变更范围/受影响模块/新增AC）；首行 DONE:。"
)
```

记录 `analyst_id`。

### 1.2 等待

```text
wait_agent(targets=[analyst_id], timeout_ms=30000)
```

- `HEARTBEAT:` -> 更新状态
- `DONE:` -> 进入用户确认

### 1.3 用户确认闸门

main 展示“新增功能 PRD 摘要 + 影响范围”，用户确认后继续。

---

## 2) architect（增量架构设计）

### 2.1 派发

```text
spawn_agent(
  agent_type="explorer",
  message="你是 rd-architect。任务：基于已确认增量PRD，输出增量 architecture/api-contracts；标明兼容性策略与迁移风险；首行 DONE:。"
)
```

记录 `architect_id`。

### 2.2 等待

```text
wait_agent(targets=[architect_id], timeout_ms=30000)
```

`DONE:` 后检查：
- 是否明确“受影响模块”
- 是否给出“向后兼容策略”
- 是否给出“回滚方案”

---

## 3) dev 实现（按 has_frontend 决定并行）

### 3.1 派发

必派后端：

```text
spawn_agent(
  agent_type="worker",
  message="你是 rd-backend-dev。任务：在现有项目上增量实现功能；不得大范围重构；首行 DONE:；附变更文件和测试结果。"
)
```

若 `has_frontend=true`，并行派前端：

```text
spawn_agent(
  agent_type="worker",
  message="你是 rd-frontend-dev。任务：在现有前端上增量实现页面/交互；首行 DONE:；附变更文件和测试结果。"
)
```

记录 `backend_id` / `frontend_id`。

### 3.2 等待

```text
wait_agent(targets=[backend_id, frontend_id], timeout_ms=30000)
```

- 后端必需 `DONE:`
- 若有前端则需要两边都 `DONE:` 后再进入 reviewer

---

## 4) reviewer（增量改动审查）

### 4.1 派发

```text
spawn_agent(
  agent_type="explorer",
  message="你是 rd-code-reviewer。任务：审查增量变更，重点看兼容性/回归风险；首行 APPROVE: 或 REJECT:。"
)
```

记录 `reviewer_id`。

### 4.2 等待与分支

```text
wait_agent(targets=[reviewer_id], timeout_ms=30000)
```

- `APPROVE:` -> 进入 tester
- `REJECT:` -> `review_round += 1`，回退 dev：

```text
send_input(target=backend_id, message="review 退回：<阻断项>，增量修复后 DONE:")
# 有 frontend 时同样回退 frontend_id
```

`review_round > 2` -> `needs_user_decision`。

---

## 5) tester（回归 + 新功能验收）

### 5.1 派发

```text
spawn_agent(
  agent_type="worker",
  message="你是 rd-tester。任务：验证新增功能 + 关键回归；首行 PASS:/BUG:/FAIL:；BUG 必须给复现步骤。"
)
```

记录 `tester_id`。

### 5.2 等待与分支

```text
wait_agent(targets=[tester_id], timeout_ms=30000)
```

- `PASS:` -> 完成
- `BUG:` / `FAIL:` -> `test_round += 1`，回退 dev：

```text
send_input(target=backend_id, message="tester 回退：<复现步骤+期望结果>，修复后 DONE:")
# 有 frontend 时同样回退 frontend_id
```

`test_round > 2` -> `needs_user_decision`。

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

## 7) feature 场景专属检查点

在进入测试前，main 额外检查：

1. 是否仅改“受影响模块”（避免无关改动扩散）
2. 是否维持向后兼容（接口/字段/行为）
3. 是否有最小回滚方案
4. 是否覆盖关键回归测试

---

## 8) 结束清理

```text
send_input(target=analyst_id, message="流程结束，准备关闭")
send_input(target=architect_id, message="流程结束，准备关闭")
send_input(target=backend_id, message="流程结束，准备关闭")
# 如有 frontend
send_input(target=frontend_id, message="流程结束，准备关闭")
send_input(target=reviewer_id, message="流程结束，准备关闭")
send_input(target=tester_id, message="流程结束，准备关闭")

close_agent(target=analyst_id)
close_agent(target=architect_id)
close_agent(target=backend_id)
# 如有 frontend
close_agent(target=frontend_id)
close_agent(target=reviewer_id)
close_agent(target=tester_id)
```

最终输出：
- 模式：feature
- 画像：effective_profile
- has_frontend
- 回退轮次（review/test）
- 重启次数
- 结论（completed / needs_user_decision / failed）
