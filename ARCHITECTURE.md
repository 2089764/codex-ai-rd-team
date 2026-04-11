# Architecture

## 目标

提供一套最小但可扩展的 RD 协作编排内核，支持：

1. 根据 tech profile 生成角色工作队列
2. 通过 coordinator 串行调度并维护状态机
3. 持久化 runtime 状态，支持复盘与调试

## 核心模块

### 配置层

- `config/tech-profiles.json`：技术栈画像与角色关注点
- `config/role-prompts.json`：coordinator 与角色 prompt 模板

### 编排核心层（`orchestrator/`）

- `profiles.py`：profile 加载、校验、继承解析、关键词匹配
- `runtime_models.py`：运行时实体（state/item/message）
- `runtime_store.py`：JSON 持久化读写
- `state_machine.py`：任务状态流转约束
- `message_router.py`：角色链路路由
- `agent_dispatcher.py`：统一 dispatch 抽象
- `planner.py`：从 profile 构建工作队列
- `coordinator.py`：主循环（dispatch -> transition -> persist）
- `cli.py`：命令行入口（orchestrate）

## 运行流程

1. CLI 读取 objective / profile 参数
2. 解析 tech profile 并生成工作队列
3. coordinator 按状态机推进任务
4. dispatcher 调用 agent client 返回结果
5. 每步结果写入 runtime store
6. 所有任务完成后状态置为 `completed`

## 当前边界

- 当前 `EchoAgentClient` 为本地占位实现，用于跑通端到端流程
- 暂未接入外部 LLM / 多 agent 实际通信
- 暂未实现并发调度，仅支持串行流程

## 约定

- 新能力优先以可测试模块形式下沉到 `orchestrator/`
- 运行时产物统一落盘到 `runtime/`
- 功能变更先补测试再改实现（TDD）
