import unittest
from tempfile import TemporaryDirectory

from orchestrator.agent_dispatcher import AgentDispatchError
from orchestrator.coordinator import Coordinator
from orchestrator.runtime_models import Role, RuntimeState, WorkItem, WorkStatus, OrchestrationStatus


class FakeDispatcher:
    def __init__(self, outputs=None, fail_on=None):
        self.outputs = outputs or {}
        self.fail_on = fail_on
        self.calls = []

    def dispatch(self, item, state):
        self.calls.append(item.item_id)
        if self.fail_on == item.item_id:
            raise AgentDispatchError("simulated failure")
        return self.outputs.get(item.item_id, f"done:{item.item_id}")


class FakeStore:
    def __init__(self):
        self.saved_states = []

    def save(self, state):
        self.saved_states.append(state.to_dict())


class CoordinatorTests(unittest.TestCase):
    def test_run_happy_path_completes_all_work_items(self):
        with TemporaryDirectory() as tmpdir:
            state = RuntimeState(
                run_id="run-c1",
                profile_name="generic",
                objective="demo",
                queue=[
                    WorkItem(item_id="w1", role=Role.ANALYST, title="a", instructions="a"),
                    WorkItem(item_id="w2", role=Role.ARCHITECT, title="b", instructions="b"),
                ],
            )
            dispatcher = FakeDispatcher(outputs={"w1": "DONE: analysis", "w2": "DONE: architecture"})
            store = FakeStore()

            final_state = Coordinator(
                dispatcher=dispatcher,
                store=store,
                has_frontend=False,
                artifact_root=tmpdir,
            ).run(state)

        self.assertEqual([i.status for i in final_state.queue], [WorkStatus.COMPLETED, WorkStatus.COMPLETED])
        self.assertEqual(final_state.status, OrchestrationStatus.COMPLETED)
        self.assertEqual(final_state.step_cursor, 2)
        self.assertTrue(store.saved_states)

    def test_run_stops_and_marks_failed_when_dispatch_fails(self):
        with TemporaryDirectory() as tmpdir:
            state = RuntimeState(
                run_id="run-c2",
                profile_name="generic",
                objective="demo",
                queue=[
                    WorkItem(item_id="w1", role=Role.ANALYST, title="a", instructions="a"),
                    WorkItem(item_id="w2", role=Role.ARCHITECT, title="b", instructions="b"),
                ],
            )
            dispatcher = FakeDispatcher(fail_on="w1")
            store = FakeStore()

            final_state = Coordinator(
                dispatcher=dispatcher,
                store=store,
                has_frontend=True,
                artifact_root=tmpdir,
            ).run(state)

        self.assertEqual(final_state.queue[0].status, WorkStatus.FAILED)
        self.assertEqual(final_state.status, OrchestrationStatus.FAILED)
        self.assertEqual(final_state.queue[1].status, WorkStatus.PENDING)
        self.assertTrue(store.saved_states)

    def test_run_marks_failed_when_result_contract_invalid(self):
        with TemporaryDirectory() as tmpdir:
            state = RuntimeState(
                run_id="run-c3",
                profile_name="generic",
                objective="demo",
                queue=[
                    WorkItem(item_id="w1", role=Role.TESTER, title="t", instructions="t"),
                    WorkItem(item_id="w2", role=Role.BACKEND_DEV, title="b", instructions="b"),
                ],
            )
            dispatcher = FakeDispatcher(outputs={"w1": "DONE: not a tester contract"})
            store = FakeStore()

            final_state = Coordinator(
                dispatcher=dispatcher,
                store=store,
                has_frontend=False,
                artifact_root=tmpdir,
            ).run(state)

        self.assertEqual(final_state.status, OrchestrationStatus.FAILED)
        self.assertEqual(final_state.queue[0].status, WorkStatus.FAILED)
        self.assertIn("invalid result contract", final_state.queue[0].error or "")
        self.assertEqual(final_state.queue[1].status, WorkStatus.PENDING)
        self.assertTrue(store.saved_states)

    def test_run_writes_heartbeat_and_result_to_message_bus(self):
        class RecordingBus:
            def __init__(self):
                self.events = []

            def append(self, role, kind, content):
                self.events.append((getattr(role, "value", role), kind, content))
                return {}

            def last_event_at(self, role):
                return None

        with TemporaryDirectory() as tmpdir:
            state = RuntimeState(
                run_id="run-c4",
                profile_name="generic",
                objective="demo",
                queue=[
                    WorkItem(item_id="w1", role=Role.ANALYST, title="a", instructions="a"),
                ],
            )
            dispatcher = FakeDispatcher(outputs={"w1": "DONE: analysis"})
            store = FakeStore()
            bus = RecordingBus()

            final_state = Coordinator(
                dispatcher=dispatcher,
                store=store,
                has_frontend=False,
                artifact_root=tmpdir,
                message_bus=bus,
            ).run(state)

        self.assertEqual(final_state.status, OrchestrationStatus.COMPLETED)
        self.assertIn(("analyst", "heartbeat", "dispatch-start:w1"), bus.events)
        self.assertIn(("analyst", "result", "DONE: analysis"), bus.events)


if __name__ == "__main__":
    unittest.main()
