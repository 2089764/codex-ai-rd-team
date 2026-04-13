import unittest

from orchestrator.coordinator import Coordinator
from orchestrator.runtime_models import OrchestrationStatus, Role, RuntimeState, WorkItem, WorkStatus


class SequencedDispatcher:
    def __init__(self, outputs):
        self.outputs = {item_id: list(values) for item_id, values in outputs.items()}
        self.calls = []

    def dispatch(self, item, state):
        self.calls.append(item.item_id)
        values = self.outputs[item.item_id]
        if not values:
            raise AssertionError(f"no more outputs configured for {item.item_id}")
        return values.pop(0)


class FakeStore:
    def __init__(self):
        self.saved_states = []

    def save(self, state):
        self.saved_states.append(state.to_dict())


class NullArtifactWriter:
    def write_prd(self, content):
        pass

    def write_architecture(self, content):
        pass

    def write_api_contracts(self, content):
        pass

    def write_review(self, number, content):
        pass


class CoordinatorLoopTests(unittest.TestCase):
    def test_reviewer_rejects_three_times_enters_needs_user_decision(self):
        state = RuntimeState(
            run_id="run-loop-1",
            profile_name="generic",
            objective="demo",
            queue=[
                WorkItem(item_id="review-1", role=Role.CODE_REVIEWER, title="review", instructions="review"),
                WorkItem(item_id="dev-1", role=Role.BACKEND_DEV, title="dev", instructions="dev"),
            ],
        )
        dispatcher = SequencedDispatcher(
            {
                "review-1": [
                    "REJECT: first pass",
                    "REJECT: second pass",
                    "REJECT: third pass",
                ],
                "dev-1": ["DONE: dev-1"],
            }
        )
        store = FakeStore()

        final_state = Coordinator(
            dispatcher=dispatcher,
            store=store,
            has_frontend=False,
            artifact_writer=NullArtifactWriter(),
        ).run(state)

        self.assertEqual(final_state.status.value, "needs_user_decision")
        self.assertEqual(dispatcher.calls, ["review-1", "review-1", "review-1"])
        self.assertEqual(final_state.queue[0].status, WorkStatus.FAILED)
        self.assertEqual(final_state.queue[1].status, WorkStatus.PENDING)
        self.assertTrue(store.saved_states)

    def test_reviewer_rejects_then_retries_before_continuing(self):
        state = RuntimeState(
            run_id="run-loop-2",
            profile_name="generic",
            objective="demo",
            queue=[
                WorkItem(item_id="review-1", role=Role.CODE_REVIEWER, title="review", instructions="review"),
                WorkItem(item_id="dev-1", role=Role.BACKEND_DEV, title="dev", instructions="dev"),
            ],
        )
        dispatcher = SequencedDispatcher(
            {
                "review-1": [
                    "REJECT: needs revision",
                    "APPROVED: looks good",
                ],
                "dev-1": ["DONE: dev-1"],
            }
        )
        store = FakeStore()

        final_state = Coordinator(
            dispatcher=dispatcher,
            store=store,
            has_frontend=False,
            artifact_writer=NullArtifactWriter(),
        ).run(state)

        self.assertEqual(dispatcher.calls, ["review-1", "review-1", "dev-1"])
        self.assertEqual(
            [item.status for item in final_state.queue],
            [WorkStatus.COMPLETED, WorkStatus.COMPLETED],
        )
        self.assertEqual(final_state.status, OrchestrationStatus.COMPLETED)
        self.assertEqual(final_state.step_cursor, 3)
        self.assertTrue(store.saved_states)


if __name__ == "__main__":
    unittest.main()
