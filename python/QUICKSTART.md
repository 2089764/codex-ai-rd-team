# QUICKSTART（5 分钟上手）

这个项目建议你只记一个入口：`ai-rd`。

---

## 1) 准备

在仓库根目录执行：

```bash
chmod +x bin/ai-rd
```

可选：把它加入 PATH（zsh）：

```bash
echo 'export PATH="/Users/fangken/codex-ai-rd-team/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

---

## 2) 日常使用（推荐）

```bash
ai-rd "修复登录500 bug"
```

默认行为：

- `AGENT_CLIENT=auto`：能用 codex 就用 codex，否则回退 echo
- `RUNTIME_DIR=./runtime`

---

## 3) 三个高频场景模板

```bash
ai-rd "实现订单导出功能，含前端筛选"
ai-rd "修复支付回调重复入账问题，附复现步骤：..."
ai-rd "重构用户权限模块，保持外部接口不变"
```

---

## 4) 结果看哪里

每次运行后，优先看这些文件：

- `runtime/run-*.json`
- `runtime/artifacts/<run_id>/requirements/prd.md`
- `runtime/artifacts/<run_id>/design/architecture.md`
- `runtime/artifacts/<run_id>/design/api-contracts.md`
- `runtime/artifacts/<run_id>/reviews/review-1.md`
- `runtime/teams/<run_id>/inboxes/main.jsonl`（CodeBuddy 风格 inbox）

可实时轮询 main inbox：

```bash
python3 -m orchestrator.cli watch-inbox \
  --runtime-dir ./runtime \
  --run-id <run_id> \
  --recipient main
```

---

## 5) 团队统一命令（不想记脚本时）

```bash
make rd OBJ="修复登录500 bug"
make rd-echo OBJ="修复登录500 bug"
make test
make sync-profiles
```

---

## 6) 可选环境变量

```bash
export AGENT_CLIENT=codex
export CODEX_MODEL=gpt-5.4
export RD_PROFILE=generic
export RUNTIME_DIR=./runtime
export TARGET_WORKDIR=$PWD
```

然后继续使用：

```bash
ai-rd "你的目标"
```

> `TARGET_WORKDIR` 用于指定实际业务项目目录。  
> 默认是你执行 `ai-rd` 时的当前目录。

---

## 7) 在 Cursor 里一键运行（Run Task）

本仓库已内置 `/.vscode/tasks.json`，可直接在 Cursor 执行：

1. 按 `Cmd + Shift + P`
2. 输入并选择 `Tasks: Run Task`
3. 选择任务：
   - `ai-rd`（真实执行）
   - `ai-rd-echo`（离线演示）
   - `test`
   - `sync-profiles`
4. 选择 `ai-rd` 或 `ai-rd-echo` 时，会弹窗输入 objective
