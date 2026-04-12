# Docs Index

本目录用于存放**稳定文档**（人工维护），不用于保存每次 orchestrate 的自动产物。

## 阅读路径（按角色）

### 1) 新同学 / 首次接触项目

1. 仓库根目录 `README.md`
2. 仓库根目录 `QUICKSTART.md`
3. 仓库根目录 `ARCHITECTURE.md`

### 2) 日常开发 / 维护者

1. `ARCHITECTURE.md`
2. `docs/design/architecture.md`
3. `docs/design/api-contracts.md`
4. `docs/reviews/review-1.md`

### 3) 外部评审 / 对外展示

1. `README.md`
2. `ARCHITECTURE.md`
3. `docs/design/architecture.md`

## 边界说明（混合模式）

- **稳定文档（本目录）**：长期沉淀、人工维护、用于对齐团队共识
- **执行产物（运行时）**：`runtime/artifacts/<run_id>/...`
- **运行态快照**：`runtime/run-*.json`

> 如果你在排查某次执行，请优先查看对应 `run_id` 的 `runtime/` 内容，而不是本目录。
