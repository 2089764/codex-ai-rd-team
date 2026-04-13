import tempfile
import unittest
from pathlib import Path

from orchestrator.coordinator import Coordinator
from orchestrator.message_bus import MessageBus
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


class CoordinatorRecoveryTests(unittest.TestCase):
    def test_timeout_redispatch_can_complete_work(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = MessageBus(Path(tmpdir), time_fn=lambda: 90.0)
            bus.append("analyst", "heartbeat", "stale")

            state = RuntimeState(
                run_id="run-recovery-1",
                profile_name="generic",
                objective="demo",
                queue=[
                    WorkItem(
                        item_id="w1",
                        role=Role.ANALYST,
                        title="a",
                        instructions="a",
                        status=WorkStatus.IN_PROGRESS,
                    ),
                    WorkItem(item_id="w2", role=Role.BACKEND_DEV, title="b", instructions="b"),
                ],
            )
            dispatcher = SequencedDispatcher({"w1": ["DONE: analysis"], "w2": ["DONE: w2"]})
            store = FakeStore()

            final_state = Coordinator(
                dispatcher=dispatcher,
                store=store,
                has_frontend=False,
                artifact_writer=NullArtifactWriter(),
                message_bus=bus,
                time_fn=lambda: 100.0,
                heartbeat_timeout_sec=5.0,
                max_redispatch=2,
            ).run(state)

            self.assertEqual(dispatcher.calls, ["w1", "w2"])
            self.assertEqual(
                [item.status for item in final_state.queue],
                [WorkStatus.COMPLETED, WorkStatus.COMPLETED],
            )
            self.assertEqual(final_state.status, OrchestrationStatus.COMPLETED)
            self.assertEqual(final_state.queue[0].attempts, 1)
            self.assertTrue(store.saved_states)

    def test_timeout_over_limit_fails_and_stops(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = MessageBus(Path(tmpdir), time_fn=lambda: 90.0)
            bus.append("analyst", "heartbeat", "stale")

            state = RuntimeState(
                run_id="run-recovery-2",
                profile_name="generic",
                objective="demo",
                queue=[
                    WorkItem(
                        item_id="w1",
                        role=Role.ANALYST,
                        title="a",
                        instructions="a",
                        status=WorkStatus.IN_PROGRESS,
                    ),
                    WorkItem(item_id="w2", role=Role.BACKEND_DEV, title="b", instructions="b"),
                ],
            )
            dispatcher = SequencedDispatcher({"w1": ["DONE: analysis"], "w2": ["DONE: w2"]})
            store = FakeStore()

            final_state = Coordinator(
                dispatcher=dispatcher,
                store=store,
                has_frontend=False,
                artifact_writer=NullArtifactWriter(),
                message_bus=bus,
                time_fn=lambda: 100.0,
                heartbeat_timeout_sec=5.0,
                max_redispatch=0,
            ).run(state)

            self.assertEqual(dispatcher.calls, [])
            self.assertEqual(final_state.status, OrchestrationStatus.FAILED)
            self.assertEqual(final_state.queue[0].status, WorkStatus.FAILED)
            self.assertEqual(final_state.queue[1].status, WorkStatus.PENDING)
            self.assertTrue(store.saved_states)


if __name__ == "__main__":
    unittest.main()
