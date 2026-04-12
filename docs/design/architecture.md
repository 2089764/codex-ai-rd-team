# 设计说明：Architecture Baseline（稳定文档）

## 1. 设计原则

1. **单一执行真相**：编排算法仅在 `orchestrator/` 实现。  
2. **配置驱动行为**：模式、画像、提示词均从配置与 objective 推导。  
3. **状态可验证**：每个 WorkItem 都有明确状态迁移和终态。  
4. **失败可恢复**：支持反馈重试与心跳超时重派。  
5. **文档与产物分离**：稳定文档在 `docs/`，自动产物在 `runtime/artifacts/`。

## 2. 模块职责

- `mode_classifier.py`：objective → mode
- `profiles.py`：画像解析、继承与匹配
- `planner.py`：画像 role_focus → WorkItem 列表
- `workflow.py`：mode + has_frontend → 角色流
- `coordinator.py`：主循环、重试、终态判定
- `agent_clients.py`：Codex/Echo 执行后端
- `runtime_store.py`：运行态 JSON 持久化
- `artifacts.py`：执行产物写入（run 级目录）

## 3. 关键设计决策（ADR 摘要）

### ADR-001：采用 “Python 内核 + A1 兼容层”
- 决策：`orchestrator/` 为唯一内核；`rd-team/` 只保留兼容入口与资源。
- 价值：减少双实现漂移，便于测试与演进。

### ADR-002：运行产物按 run_id 隔离
- 决策：自动产物写入 `runtime/artifacts/<run_id>/...`。
- 价值：避免覆盖稳定文档，提升可追溯性。

### ADR-003：反馈闭环优先于“一次成功”
- 决策：reviewer/tester 负反馈会触发重试，并设置上限保护。
- 价值：在失败可控前提下提升最终质量。

## 4. 版本约束

- 当前版本：`v0.1.x`
- 本文档为稳定说明，非运行时自动产物
