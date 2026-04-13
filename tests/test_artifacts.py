import tempfile
import unittest
from pathlib import Path

from orchestrator.coordinator import Coordinator
from orchestrator.runtime_models import OrchestrationStatus, Role, RuntimeState, WorkItem, WorkStatus
from orchestrator.artifacts import ArtifactWriter


class ArtifactWriterTests(unittest.TestCase):
    def test_write_standard_a_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = ArtifactWriter(Path(tmpdir))

            prd_path = writer.write_prd("PRD")
            architecture_path = writer.write_architecture("ARCH")
            api_contracts_path = writer.write_api_contracts("API")
            review_path = writer.write_review(1, "REVIEW")

            expected = {
                "requirements/prd.md": ("PRD", prd_path),
                "design/architecture.md": ("ARCH", architecture_path),
                "design/api-contracts.md": ("API", api_contracts_path),
                "reviews/review-1.md": ("REVIEW", review_path),
            }

            for rel_path, (content, actual_path) in expected.items():
                with self.subTest(path=rel_path):
                    path = Path(tmpdir) / rel_path
                    self.assertEqual(actual_path, path)
                    self.assertTrue(path.exists())
                    self.assertEqual(path.read_text(encoding="utf-8"), content)

    def test_coordinator_writes_standard_a_artifacts_by_role(self):
        class FakeDispatcher:
            def __init__(self):
                self.calls = []

            def dispatch(self, item, state):
                self.calls.append(item.item_id)
                if item.role == Role.CODE_REVIEWER:
                    return f"APPROVE: result:{item.item_id}"
                if item.role == Role.TESTER:
                    return f"PASS: result:{item.item_id}"
                return f"DONE: result:{item.item_id}"

        class FakeStore:
            def __init__(self):
                self.saved_states = []

            def save(self, state):
                self.saved_states.append(state.to_dict())

        class RecordingArtifactWriter:
            def __init__(self):
                self.calls = []

            def write_prd(self, content):
                self.calls.append(("prd", content))

            def write_architecture(self, content):
                self.calls.append(("architecture", content))

            def write_api_contracts(self, content):
                self.calls.append(("api-contracts", content))

            def write_review(self, number, content):
                self.calls.append((f"review-{number}", content))

        state = RuntimeState(
            run_id="run-artifacts-1",
            profile_name="generic",
            objective="demo",
            queue=[
                WorkItem(item_id="w1", role=Role.ANALYST, title="a", instructions="a"),
                WorkItem(item_id="w2", role=Role.ARCHITECT, title="b", instructions="b"),
                WorkItem(item_id="w3", role=Role.CODE_REVIEWER, title="c", instructions="c"),
            ],
        )
        dispatcher = FakeDispatcher()
        store = FakeStore()
        writer = RecordingArtifactWriter()

        final_state = Coordinator(
            dispatcher=dispatcher,
            store=store,
            has_frontend=False,
            artifact_writer=writer,
        ).run(state)

        self.assertEqual(
            writer.calls,
            [
                ("prd", "DONE: result:w1"),
                ("architecture", "DONE: result:w2"),
                ("api-contracts", "DONE: result:w2"),
                ("review-1", "APPROVE: result:w3"),
            ],
        )
        self.assertEqual(
            [item.status for item in final_state.queue],
            [WorkStatus.COMPLETED, WorkStatus.COMPLETED, WorkStatus.COMPLETED],
        )
        self.assertEqual(final_state.status, OrchestrationStatus.COMPLETED)
        self.assertEqual(final_state.step_cursor, 3)
        self.assertEqual(len(store.saved_states), 1)

    def test_coordinator_continues_when_artifact_write_fails(self):
        class FakeDispatcher:
            def __init__(self):
                self.calls = []

            def dispatch(self, item, state):
                self.calls.append(item.item_id)
                if item.role == Role.CODE_REVIEWER:
                    return f"APPROVE: result:{item.item_id}"
                if item.role == Role.TESTER:
                    return f"PASS: result:{item.item_id}"
                return f"DONE: result:{item.item_id}"

        class FakeStore:
            def __init__(self):
                self.saved_states = []

            def save(self, state):
                self.saved_states.append(state.to_dict())

        class FailingArtifactWriter:
            def __init__(self):
                self.calls = []

            def write_prd(self, content):
                self.calls.append(("prd", content))
                raise RuntimeError("artifact write failed")

            def write_architecture(self, content):
                self.calls.append(("architecture", content))

            def write_api_contracts(self, content):
                self.calls.append(("api-contracts", content))

            def write_review(self, number, content):
                self.calls.append((f"review-{number}", content))

        state = RuntimeState(
            run_id="run-artifacts-2",
            profile_name="generic",
            objective="demo",
            queue=[
                WorkItem(item_id="w1", role=Role.ANALYST, title="a", instructions="a"),
                WorkItem(item_id="w2", role=Role.ARCHITECT, title="b", instructions="b"),
            ],
        )
        dispatcher = FakeDispatcher()
        store = FakeStore()
        writer = FailingArtifactWriter()

        final_state = Coordinator(
            dispatcher=dispatcher,
            store=store,
            has_frontend=True,
            artifact_writer=writer,
        ).run(state)

        self.assertEqual(writer.calls[0], ("prd", "DONE: result:w1"))
        self.assertEqual(
            [item.status for item in final_state.queue],
            [WorkStatus.COMPLETED, WorkStatus.COMPLETED],
        )
        self.assertEqual(final_state.status, OrchestrationStatus.COMPLETED)
        self.assertEqual(final_state.step_cursor, 2)
        self.assertEqual(len(final_state.messages), 2)
        self.assertEqual(len(store.saved_states), 1)
        self.assertEqual(store.saved_states[0]["status"], OrchestrationStatus.COMPLETED.value)

    def test_coordinator_review_artifacts_use_incremental_number(self):
        class FakeDispatcher:
            def __init__(self):
                self.calls = []

            def dispatch(self, item, state):
                self.calls.append(item.item_id)
                if item.role == Role.CODE_REVIEWER:
                    return f"APPROVE: result:{item.item_id}"
                if item.role == Role.TESTER:
                    return f"PASS: result:{item.item_id}"
                return f"DONE: result:{item.item_id}"

        class FakeStore:
            def __init__(self):
                self.saved_states = []

            def save(self, state):
                self.saved_states.append(state.to_dict())

        class RecordingArtifactWriter:
            def __init__(self):
                self.calls = []

            def write_prd(self, content):
                self.calls.append(("prd", content))

            def write_architecture(self, content):
                self.calls.append(("architecture", content))

            def write_api_contracts(self, content):
                self.calls.append(("api-contracts", content))

            def write_review(self, number, content):
                self.calls.append((f"review-{number}", content))

        state = RuntimeState(
            run_id="run-artifacts-3",
            profile_name="generic",
            objective="demo",
            queue=[
                WorkItem(item_id="review-1", role=Role.CODE_REVIEWER, title="r1", instructions="r1"),
                WorkItem(item_id="review-2", role=Role.CODE_REVIEWER, title="r2", instructions="r2"),
            ],
        )
        dispatcher = FakeDispatcher()
        store = FakeStore()
        writer = RecordingArtifactWriter()

        final_state = Coordinator(
            dispatcher=dispatcher,
            store=store,
            has_frontend=False,
            artifact_writer=writer,
        ).run(state)

        self.assertEqual(
            writer.calls,
            [
                ("review-1", "APPROVE: result:review-1"),
                ("review-2", "APPROVE: result:review-2"),
            ],
        )
        self.assertEqual(final_state.status, OrchestrationStatus.COMPLETED)
        self.assertEqual(len(store.saved_states), 1)


if __name__ == "__main__":
    unittest.main()
