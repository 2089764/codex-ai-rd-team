# B+A1 完整功能实现 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有 Python 内核上实现 ai-rd-team 的完整行为（6 角色 + 4 模式 + 回退闭环 + 心跳重派 + 标准 A 产物），并补齐 A1 兼容层 `rd-team/` 目录与入口语义。

**Architecture:** 采用“单一执行内核 + 兼容适配层”架构：所有业务流程仅在 `orchestrator/` 实现；`rd-team/` 仅提供兼容目录与命令入口，转调 Python CLI，避免双实现漂移。状态与事件统一落在 `runtime/`，产物统一落在 `docs/`。

**Tech Stack:** Python 3.11+、unittest、JSON 文件存储、Typer/argparse（CLI 双入口）。

---

### Task 1: 模式判定器（4 模式）

**Files:**
- Create: `orchestrator/mode_classifier.py`
- Test: `tests/test_mode_classifier.py`

- [ ] **Step 1: 写失败测试（模式优先级与默认行为）**

```python
# tests/test_mode_classifier.py
import unittest
from orchestrator.mode_classifier import classify_mode

class ModeClassifierTests(unittest.TestCase):
    def test_bugfix_priority_over_feature(self):
        self.assertEqual(classify_mode("给登录接口加重试并修复500 bug"), "bugfix")

    def test_refactor_priority_over_feature(self):
        self.assertEqual(classify_mode("新增字段并重构数据层"), "refactor")

    def test_feature(self):
        self.assertEqual(classify_mode("给现有系统新增导出功能"), "feature")

    def test_new_project_default(self):
        self.assertEqual(classify_mode("做一个用户系统"), "new_project")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m unittest -v tests/test_mode_classifier.py`
Expected: `ModuleNotFoundError: No module named 'orchestrator.mode_classifier'`

- [ ] **Step 3: 最小实现**

```python
# orchestrator/mode_classifier.py
BUGFIX = ("修复", "bug", "报错", "异常")
REFACTOR = ("重构", "优化", "改造", "重写")
FEATURE = ("新增", "加一个", "扩展")
NEW_PROJECT = ("做一个", "创建", "从零")

def classify_mode(text: str) -> str:
    t = (text or "").lower()
    if any(k in t for k in BUGFIX):
        return "bugfix"
    if any(k in t for k in REFACTOR):
        return "refactor"
    if any(k in t for k in FEATURE):
        return "feature"
    if any(k in t for k in NEW_PROJECT):
        return "new_project"
    return "new_project"
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python3 -m unittest -v tests/test_mode_classifier.py`
Expected: 4 passed

- [ ] **Step 5: 提交**

```bash
git add orchestrator/mode_classifier.py tests/test_mode_classifier.py
git commit -m "feat: add mode classifier for 4 rd-team scenarios"
```

### Task 2: 工作流生成器（6 角色 + has_frontend）

**Files:**
- Create: `orchestrator/workflow.py`
- Test: `tests/test_workflow.py`

- [ ] **Step 1: 写失败测试（四种模式角色序列）**

```python
# tests/test_workflow.py
import unittest
from orchestrator.workflow import build_role_flow

class WorkflowTests(unittest.TestCase):
    def test_new_project_with_frontend(self):
        self.assertEqual(
            build_role_flow(mode="new_project", has_frontend=True),
            ["analyst", "architect", "backend-dev", "frontend-dev", "code-reviewer", "tester"],
        )

    def test_bugfix_api_only(self):
        self.assertEqual(
            build_role_flow(mode="bugfix", has_frontend=False),
            ["backend-dev", "code-reviewer", "tester"],
        )
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m unittest -v tests/test_workflow.py`
Expected: `ModuleNotFoundError: No module named 'orchestrator.workflow'`

- [ ] **Step 3: 最小实现**

```python
# orchestrator/workflow.py
def build_role_flow(*, mode: str, has_frontend: bool) -> list[str]:
    if mode == "bugfix":
        return ["backend-dev", "code-reviewer", "tester"]
    if mode == "refactor":
        seq = ["architect", "backend-dev"]
        if has_frontend:
            seq.append("frontend-dev")
        return [*seq, "code-reviewer", "tester"]
    if mode == "feature":
        seq = ["analyst", "architect", "backend-dev"]
        if has_frontend:
            seq.append("frontend-dev")
        return [*seq, "code-reviewer", "tester"]
    seq = ["analyst", "architect", "backend-dev"]
    if has_frontend:
        seq.append("frontend-dev")
    return [*seq, "code-reviewer", "tester"]
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python3 -m unittest -v tests/test_workflow.py`
Expected: 2 passed

- [ ] **Step 5: 提交**

```bash
git add orchestrator/workflow.py tests/test_workflow.py
git commit -m "feat: add role workflow builder for rd-team modes"
```

### Task 3: 标准 A 产物写入器（PRD/设计/API/Review）

**Files:**
- Create: `orchestrator/artifacts.py`
- Test: `tests/test_artifacts.py`
- Modify: `orchestrator/coordinator.py`

- [ ] **Step 1: 写失败测试（产物路径与内容）**

```python
# tests/test_artifacts.py
import tempfile
import unittest
from pathlib import Path
from orchestrator.artifacts import ArtifactWriter

class ArtifactWriterTests(unittest.TestCase):
    def test_write_standard_a_files(self):
        with tempfile.TemporaryDirectory() as d:
            writer = ArtifactWriter(Path(d))
            writer.write_prd("PRD")
            writer.write_architecture("ARCH")
            writer.write_api_contracts("API")
            writer.write_review(1, "REVIEW")
            self.assertEqual((Path(d) / "requirements/prd.md").read_text(encoding="utf-8"), "PRD")
            self.assertEqual((Path(d) / "design/architecture.md").read_text(encoding="utf-8"), "ARCH")
            self.assertEqual((Path(d) / "design/api-contracts.md").read_text(encoding="utf-8"), "API")
            self.assertEqual((Path(d) / "reviews/review-1.md").read_text(encoding="utf-8"), "REVIEW")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m unittest -v tests/test_artifacts.py`
Expected: `ModuleNotFoundError: No module named 'orchestrator.artifacts'`

- [ ] **Step 3: 最小实现 + 在 coordinator 接入**

```python
# orchestrator/artifacts.py
from pathlib import Path

class ArtifactWriter:
    def __init__(self, docs_root: Path):
        self.docs_root = docs_root

    def _write(self, rel: str, content: str) -> Path:
        path = self.docs_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def write_prd(self, content: str):
        return self._write("requirements/prd.md", content)

    def write_architecture(self, content: str):
        return self._write("design/architecture.md", content)

    def write_api_contracts(self, content: str):
        return self._write("design/api-contracts.md", content)

    def write_review(self, n: int, content: str):
        return self._write(f"reviews/review-{n}.md", content)
```

```python
# coordinator.py 接入示例（完整函数）
from pathlib import Path
from orchestrator.artifacts import ArtifactWriter
from orchestrator.runtime_models import Role

def persist_artifact_by_role(role: Role, content: str) -> None:
    writer = ArtifactWriter(Path("docs"))
    if role == Role.ANALYST:
        writer.write_prd(content)
    elif role == Role.ARCHITECT:
        writer.write_architecture(content)
        writer.write_api_contracts(content)
    elif role == Role.CODE_REVIEWER:
        writer.write_review(1, content)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python3 -m unittest -v tests/test_artifacts.py`
Expected: 1 passed

- [ ] **Step 5: 提交**

```bash
git add orchestrator/artifacts.py orchestrator/coordinator.py tests/test_artifacts.py
git commit -m "feat: add standard-A artifact writer and coordinator integration"
```

### Task 4: 回退闭环与轮次上限（review/test）

**Files:**
- Modify: `orchestrator/runtime_models.py`
- Modify: `orchestrator/coordinator.py`
- Test: `tests/test_coordinator_loops.py`

- [ ] **Step 1: 写失败测试（最多 2 轮）**

```python
# tests/test_coordinator_loops.py
import unittest
from orchestrator.runtime_models import RuntimeState, WorkItem, Role, OrchestrationStatus
from orchestrator.coordinator import Coordinator

class RejectingDispatcher:
    def __init__(self):
        self.review_count = 0
    def dispatch(self, item, state):
        if item.role == Role.BACKEND_DEV:
            return "implemented"
        if item.role == Role.CODE_REVIEWER:
            self.review_count += 1
            return "REJECT: style issue"
        return "ok"

class NoopStore:
    def save(self, state):
        return None

class LoopTests(unittest.TestCase):
    def test_reviewer_reject_exceeds_limit_to_needs_user_decision(self):
        state = RuntimeState(
            run_id="run-loop",
            profile_name="generic",
            objective="demo",
            queue=[
                WorkItem(item_id="w1", role=Role.BACKEND_DEV, title="impl", instructions="impl"),
                WorkItem(item_id="w2", role=Role.CODE_REVIEWER, title="review", instructions="review"),
            ],
        )
        final_state = Coordinator(
            dispatcher=RejectingDispatcher(),
            store=NoopStore(),
            has_frontend=False,
        ).run(state)
        self.assertEqual(final_state.status, OrchestrationStatus.NEEDS_USER_DECISION)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m unittest -v tests/test_coordinator_loops.py`
Expected: FAIL，提示 `OrchestrationStatus` 暂无 `NEEDS_USER_DECISION` 或流程未进入该状态

- [ ] **Step 3: 最小实现（新增状态 + 回退计数）**

```python
# runtime_models.py
class OrchestrationStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_USER_DECISION = "needs_user_decision"

# coordinator.py
MAX_REVIEW_RETRY = 2
def _handle_review_result(text: str, retry: int) -> tuple[bool, bool]:
    is_reject = text.startswith("REJECT:")
    if not is_reject:
        return True, False
    if retry >= MAX_REVIEW_RETRY:
        return False, True
    return False, False
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python3 -m unittest -v tests/test_coordinator_loops.py`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add orchestrator/runtime_models.py orchestrator/coordinator.py tests/test_coordinator_loops.py
git commit -m "feat: add review/test feedback loops with retry caps"
```

### Task 5: 心跳/邮箱总线与超时重派

**Files:**
- Create: `orchestrator/message_bus.py`
- Modify: `orchestrator/coordinator.py`
- Test: `tests/test_message_bus.py`
- Test: `tests/test_coordinator_recovery.py`

- [ ] **Step 1: 写失败测试（heartbeat + timeout）**

```python
# tests/test_message_bus.py
import tempfile
import unittest
from pathlib import Path
from orchestrator.message_bus import MessageBus

class MessageBusTests(unittest.TestCase):
    def test_append_and_read_events(self):
        with tempfile.TemporaryDirectory() as d:
            bus = MessageBus(Path(d))
            bus.append("backend-dev", "heartbeat", "alive")
            events = bus.read("backend-dev")
            self.assertEqual(events[-1]["kind"], "heartbeat")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m unittest -v tests/test_message_bus.py`
Expected: `ModuleNotFoundError`

- [ ] **Step 3: 最小实现 + 协调者重派策略**

```python
# orchestrator/message_bus.py
import json, time
from pathlib import Path

class MessageBus:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def append(self, role: str, kind: str, content: str):
        p = self.root / f"{role}.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), "kind": kind, "content": content}, ensure_ascii=False) + "\n")

    def read(self, role: str) -> list[dict]:
        p = self.root / f"{role}.jsonl"
        if not p.exists():
            return []
        return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
```

```python
# coordinator.py 关键逻辑
HEARTBEAT_TIMEOUT = 150
MAX_REDISPATCH = 2
# 若 role 最近事件超过 HEARTBEAT_TIMEOUT 秒未更新：
# 1) redispatch_count += 1
# 2) redispatch_count > MAX_REDISPATCH -> state.status = FAILED
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python3 -m unittest -v tests/test_message_bus.py tests/test_coordinator_recovery.py`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add orchestrator/message_bus.py orchestrator/coordinator.py tests/test_message_bus.py tests/test_coordinator_recovery.py
git commit -m "feat: add message bus heartbeat and timeout redispatch"
```

### Task 6: CLI 增强（mode + 产物 + A1 转调支持）

**Files:**
- Modify: `orchestrator/cli.py`
- Create: `tests/test_cli_modes_e2e.py`

- [ ] **Step 1: 写失败测试（四模式入口）**

```python
# tests/test_cli_modes_e2e.py
import io
import unittest
from contextlib import redirect_stdout
from orchestrator.cli import main

class CliModesTests(unittest.TestCase):
    def test_bugfix_mode(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["orchestrate", "--objective", "修复登录500 bug"])
        self.assertEqual(code, 0)
        self.assertIn("mode=bugfix", out.getvalue())
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m unittest -v tests/test_cli_modes_e2e.py`
Expected: FAIL（输出无 mode）

- [ ] **Step 3: 最小实现**

```python
# cli.py 关键实现
from orchestrator.mode_classifier import classify_mode

mode = classify_mode(objective)
print(
    f"run_id={final_state.run_id} mode={mode} profile={final_state.profile_name} "
    f"status={final_state.status.value} steps={final_state.step_cursor}"
)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python3 -m unittest -v tests/test_cli_modes_e2e.py`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add orchestrator/cli.py tests/test_cli_modes_e2e.py
git commit -m "feat: add mode-aware orchestration cli output and flow"
```

### Task 7: A1 兼容层目录与资源同步

**Files:**
- Create: `rd-team/SKILL.md`
- Create: `rd-team/commands/rd-team.md`
- Create: `rd-team/agents/analyst.md`
- Create: `rd-team/agents/architect.md`
- Create: `rd-team/agents/backend-dev.md`
- Create: `rd-team/agents/frontend-dev.md`
- Create: `rd-team/agents/code-reviewer.md`
- Create: `rd-team/agents/tester.md`
- Create: `rd-team/shared-rd-resources/tech-profiles/tech-profiles.json`
- Create: `scripts/sync_tech_profiles.py`
- Test: `tests/test_a1_layout.py`

- [ ] **Step 1: 写失败测试（目录完整性）**

```python
# tests/test_a1_layout.py
from pathlib import Path
import unittest

class A1LayoutTests(unittest.TestCase):
    def test_required_files_exist(self):
        required = [
            "rd-team/SKILL.md",
            "rd-team/commands/rd-team.md",
            "rd-team/agents/analyst.md",
            "rd-team/shared-rd-resources/tech-profiles/tech-profiles.json",
        ]
        for rel in required:
            self.assertTrue(Path(rel).exists(), rel)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m unittest -v tests/test_a1_layout.py`
Expected: FAIL（文件不存在）

- [ ] **Step 3: 最小实现（兼容目录 + 转调说明）**

```md
# rd-team/commands/rd-team.md（核心内容）
# 解析 /rd-team 参数后，执行：
# python -m orchestrator.cli orchestrate --objective "{用户输入}"
```

```python
# scripts/sync_tech_profiles.py
import json
from pathlib import Path
src = Path("config/tech-profiles.json")
dst = Path("rd-team/shared-rd-resources/tech-profiles/tech-profiles.json")
dst.parent.mkdir(parents=True, exist_ok=True)
dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python3 scripts/sync_tech_profiles.py && python3 -m unittest -v tests/test_a1_layout.py`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add rd-team scripts/sync_tech_profiles.py tests/test_a1_layout.py
git commit -m "feat: add A1 compatible rd-team package and tech profile sync"
```

### Task 8: 全量验证与文档收尾

**Files:**
- Modify: `README.md`
- Modify: `ARCHITECTURE.md`
- Modify: `docs/superpowers/specs/2026-04-12-rd-team-b-plus-a1-design.md`（如实现偏差说明）

- [ ] **Step 1: 更新 README（B 主体 + A1 兼容）**

```md
# README 增补
- 4 模式说明
- 标准 A 产物路径
- /rd-team 兼容层说明
- Cursor 使用方式
```

- [ ] **Step 2: 运行全量测试**

Run: `python3 -m unittest discover -s tests -v`
Expected: 全部 PASS

- [ ] **Step 3: 运行端到端验收命令（至少 2 模式）**

Run:
- `python3 -m orchestrator.cli orchestrate --objective "做一个用户系统" --runtime-dir ./runtime`
- `python3 -m orchestrator.cli orchestrate --objective "修复登录500 bug" --runtime-dir ./runtime`

Expected: 输出包含 `status=completed`，并生成 `docs/requirements`/`docs/design`/`docs/reviews` 与 `runtime/run-*.json`

- [ ] **Step 4: 质量检查**

Run:
- `python3 -m py_compile orchestrator/*.py`
- `rg -n "TODO|TBD|FIXME" orchestrator rd-team docs README.md ARCHITECTURE.md tests || true`

Expected: 编译通过；无遗留占位

- [ ] **Step 5: 最终提交**

```bash
git add README.md ARCHITECTURE.md docs/superpowers/specs/2026-04-12-rd-team-b-plus-a1-design.md
git add orchestrator rd-team tests scripts config
git commit -m "feat: complete rd-team full functionality with B core and A1 compatibility"
```
