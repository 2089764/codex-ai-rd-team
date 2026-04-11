import tempfile
import unittest
from pathlib import Path

from orchestrator.runtime_models import OrchestrationStatus, Role, RuntimeState, WorkItem
from orchestrator.runtime_store import RuntimeStore


class RuntimeStoreTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.store = RuntimeStore(Path(self.tempdir.name))

    def tearDown(self):
        self.tempdir.cleanup()

    def test_save_and_load_round_trip(self):
        state = RuntimeState(
            run_id="run-a",
            profile_name="generic",
            objective="demo",
            status=OrchestrationStatus.RUNNING,
            queue=[
                WorkItem(
                    item_id="w1",
                    role=Role.ANALYST,
                    title="分析",
                    instructions="拆解",
                )
            ],
        )

        path = self.store.save(state)
        loaded = self.store.load("run-a")

        self.assertTrue(path.exists())
        self.assertEqual(loaded, state)

    def test_load_missing_run_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            self.store.load("missing-run")

    def test_list_run_ids_is_sorted_and_ignores_non_json(self):
        state_b = RuntimeState(run_id="run-b", profile_name="generic", objective="b")
        state_a = RuntimeState(run_id="run-a", profile_name="generic", objective="a")

        self.store.save(state_b)
        self.store.save(state_a)
        (Path(self.tempdir.name) / "README.txt").write_text("ignore me", encoding="utf-8")

        self.assertEqual(self.store.list_run_ids(), ["run-a", "run-b"])


if __name__ == "__main__":
    unittest.main()
