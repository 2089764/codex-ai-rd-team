# codex-ai-rd-team

一个面向 RD 协作编排的 Python 项目。

## 当前能力

- tech profile 配置加载与解析（继承、关键词匹配、结构校验）
- 核心运行时模型（`RuntimeState` / `WorkItem` / `RoutedMessage`）
- runtime JSON 存储层（保存、加载、列举）
- 状态机（任务推进、完成、失败转换）
- 消息路由（按角色链路推进行为）
- agent dispatcher（统一 dispatch 接口）
- coordinator 主循环（串行调度 + 状态落盘）
- 角色与 coordinator prompt 模板
- CLI 端到端执行（`orchestrate`）

## 目录概览

```text
codex-ai-rd-team/
├── config/
│   ├── role-prompts.json
│   └── tech-profiles.json
├── orchestrator/
│   ├── __init__.py
│   ├── agent_dispatcher.py
│   ├── cli.py
│   ├── coordinator.py
│   ├── message_router.py
│   ├── planner.py
│   ├── profiles.py
│   ├── prompts.py
│   ├── runtime_models.py
│   ├── runtime_store.py
│   └── state_machine.py
├── runtime/
└── tests/
```

## CLI 用法

```bash
python -m orchestrator.cli orchestrate \
  --objective "build a kratos api service" \
  --runtime-dir ./runtime
```

示例输出：

```text
run_id=run-20260411235959 profile=go-kratos-api status=completed steps=6
```

## 测试

```bash
python3 -m unittest discover -s tests -v
```
