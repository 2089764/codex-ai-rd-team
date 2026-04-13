import unittest

from orchestrator.runtime_models import (
    OrchestrationStatus,
    Role,
    RoutedMessage,
    RuntimeState,
    WorkItem,
    WorkStatus,
)


class RuntimeModelsTests(unittest.TestCase):
    def test_runtime_state_round_trip(self):
        state = RuntimeState(
            run_id="run-001",
            profile_name="go-kratos-web",
            objective="build user center",
            status=OrchestrationStatus.RUNNING,
            queue=[
                WorkItem(
                    item_id="w1",
                    role=Role.ANALYST,
                    title="拆解需求",
                    instructions="产出需求清单",
                    status=WorkStatus.COMPLETED,
                    result="完成",
                    attempts=1,
                ),
                WorkItem(
                    item_id="w2",
                    role=Role.ARCHITECT,
                    title="给出架构",
                    instructions="输出模块边界",
                    status=WorkStatus.PENDING,
                ),
            ],
            messages=[
                RoutedMessage(
                    sender="coordinator",
                    recipient="analyst",
                    kind="dispatch",
                    content="请先拆需求",
                    work_item_id="w1",
                )
            ],
            shared_context={"repo": "codex-ai-rd-team"},
            step_cursor=1,
        )

        payload = state.to_dict()
        restored = RuntimeState.from_dict(payload)

        self.assertEqual(restored, state)

    def test_next_pending_item_returns_first_pending(self):
        state = RuntimeState(
            run_id="run-002",
            profile_name="generic",
            objective="demo",
            queue=[
                WorkItem(
                    item_id="w1",
                    role=Role.ANALYST,
                    title="a",
                    instructions="a",
                    status=WorkStatus.COMPLETED,
                ),
                WorkItem(
                    item_id="w2",
                    role=Role.BACKEND_DEV,
                    title="b",
                    instructions="b",
                    status=WorkStatus.PENDING,
                ),
            ],
        )

        pending = state.next_pending_item()

        self.assertIsNotNone(pending)
        self.assertEqual(pending.item_id, "w2")

    def test_mark_terminal_if_done_only_when_all_completed(self):
        state = RuntimeState(
            run_id="run-003",
            profile_name="generic",
            objective="demo",
            status=OrchestrationStatus.RUNNING,
            queue=[
                WorkItem(
                    item_id="w1",
                    role=Role.ANALYST,
                    title="a",
                    instructions="a",
                    status=WorkStatus.COMPLETED,
                ),
                WorkItem(
                    item_id="w2",
                    role=Role.BACKEND_DEV,
                    title="b",
                    instructions="b",
                    status=WorkStatus.PENDING,
                ),
            ],
        )

        changed = state.mark_terminal_if_done()

        self.assertFalse(changed)
        self.assertEqual(state.status, OrchestrationStatus.RUNNING)

        state.queue[1].status = WorkStatus.COMPLETED
        changed = state.mark_terminal_if_done()

        self.assertTrue(changed)
        self.assertEqual(state.status, OrchestrationStatus.COMPLETED)

    def test_from_dict_rejects_unknown_enum_value(self):
        payload = {
            "run_id": "run-004",
            "profile_name": "generic",
            "objective": "demo",
            "status": "running",
            "queue": [
                {
                    "item_id": "w1",
                    "role": "analyst",
                    "title": "a",
                    "instructions": "a",
                    "status": "not-a-status",
                    "result": None,
                    "error": None,
                    "attempts": 0,
                }
            ],
            "messages": [],
            "shared_context": {},
            "step_cursor": 0,
        }

        with self.assertRaises(ValueError):
            RuntimeState.from_dict(payload)


if __name__ == "__main__":
    unittest.main()
