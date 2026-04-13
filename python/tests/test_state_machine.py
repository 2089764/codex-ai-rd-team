import unittest

from orchestrator.runtime_models import (
    OrchestrationStatus,
    Role,
    RuntimeState,
    WorkItem,
    WorkStatus,
)
from orchestrator.state_machine import StateTransitionError, complete_item, fail_item, start_next_item


class StateMachineTests(unittest.TestCase):
    def _make_state(self) -> RuntimeState:
        return RuntimeState(
            run_id="run-sm-1",
            profile_name="generic",
            objective="demo",
            status=OrchestrationStatus.IDLE,
            queue=[
                WorkItem(item_id="w1", role=Role.ANALYST, title="a", instructions="a"),
                WorkItem(item_id="w2", role=Role.ARCHITECT, title="b", instructions="b"),
            ],
        )

    def test_start_next_item_moves_pending_to_in_progress(self):
        state = self._make_state()

        item = start_next_item(state)

        self.assertIsNotNone(item)
        self.assertEqual(item.item_id, "w1")
        self.assertEqual(item.status, WorkStatus.IN_PROGRESS)
        self.assertEqual(state.status, OrchestrationStatus.RUNNING)

    def test_complete_item_marks_completed_and_auto_terminal(self):
        state = self._make_state()

        start_next_item(state)
        complete_item(state, "w1", "done")
        start_next_item(state)
        complete_item(state, "w2", "done")

        self.assertEqual(state.queue[0].status, WorkStatus.COMPLETED)
        self.assertEqual(state.queue[1].status, WorkStatus.COMPLETED)
        self.assertEqual(state.status, OrchestrationStatus.COMPLETED)

    def test_fail_item_marks_item_and_run_failed(self):
        state = self._make_state()

        start_next_item(state)
        fail_item(state, "w1", "network error")

        self.assertEqual(state.queue[0].status, WorkStatus.FAILED)
        self.assertEqual(state.queue[0].error, "network error")
        self.assertEqual(state.status, OrchestrationStatus.FAILED)

    def test_invalid_transition_raises(self):
        state = self._make_state()

        with self.assertRaises(StateTransitionError):
            complete_item(state, "w1", "should fail because not in progress")


if __name__ == "__main__":
    unittest.main()
