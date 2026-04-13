# /rd-team Command

接收 `/rd-team` 参数，并转调：

```bash
python -m orchestrator.cli orchestrate --objective "<用户输入>" --agent-client auto
```

## 说明

- `/rd-team` 只负责兼容入口
- 参数解析后，不在此层重复实现编排逻辑
- 所有实际执行由 `orchestrator.cli` 负责
