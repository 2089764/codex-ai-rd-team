import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from orchestrator.cli import main


class CliModeE2ETests(unittest.TestCase):
    def _run_cli(self, objective: str) -> tuple[int, str, tempfile.TemporaryDirectory]:
        tempdir = tempfile.TemporaryDirectory()
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "orchestrate",
                    "--objective",
                    objective,
                    "--runtime-dir",
                    tempdir.name,
                    "--agent-client",
                    "echo",
                ]
            )

        return exit_code, buffer.getvalue(), tempdir

    def _load_runtime_state(self, runtime_dir: Path) -> dict:
        files = list(runtime_dir.glob("*.json"))
        self.assertEqual(len(files), 1, files)
        return json.loads(files[0].read_text(encoding="utf-8"))

    def test_bugfix_objective_reports_bugfix_mode(self):
        exit_code, output, tempdir = self._run_cli("修复登录500 bug")
        try:
            self.assertEqual(exit_code, 0, output)
            self.assertIn("mode=bugfix", output)

            state = self._load_runtime_state(Path(tempdir.name))
            self.assertEqual(
                [item["role"] for item in state["queue"]],
                ["backend-dev", "backend-dev", "code-reviewer", "tester"],
            )
        finally:
            tempdir.cleanup()

    def test_feature_objective_reports_feature_mode(self):
        exit_code, output, tempdir = self._run_cli("新增导出功能")
        try:
            self.assertEqual(exit_code, 0, output)
            self.assertIn("mode=feature", output)

            state = self._load_runtime_state(Path(tempdir.name))
            self.assertEqual(state["shared_context"]["mode"], "feature")
            self.assertEqual(state["shared_context"]["project_type"], "generic")
            self.assertEqual(state["shared_context"]["effective_profile"], "generic")
            self.assertEqual(
                [item["role"] for item in state["queue"]],
                [
                    "analyst",
                    "analyst",
                    "architect",
                    "backend-dev",
                    "backend-dev",
                    "code-reviewer",
                    "tester",
                ],
            )
        finally:
            tempdir.cleanup()

    def test_refactor_objective_reports_refactor_mode(self):
        exit_code, output, tempdir = self._run_cli("重构数据层")
        try:
            self.assertEqual(exit_code, 0, output)
            self.assertIn("mode=refactor", output)

            state = self._load_runtime_state(Path(tempdir.name))
            self.assertEqual(state["shared_context"]["mode"], "refactor")
            self.assertEqual(state["shared_context"]["project_type"], "generic")
            self.assertEqual(state["shared_context"]["effective_profile"], "generic")
        finally:
            tempdir.cleanup()

    def test_new_project_objective_reports_new_project_mode(self):
        exit_code, output, tempdir = self._run_cli("做一个用户系统")
        try:
            self.assertEqual(exit_code, 0, output)
            self.assertIn("mode=new_project", output)

            state = self._load_runtime_state(Path(tempdir.name))
            self.assertEqual(state["shared_context"]["mode"], "new_project")
            self.assertEqual(state["shared_context"]["project_type"], "generic")
            self.assertEqual(state["shared_context"]["effective_profile"], "generic")
            self.assertIn("execution_stages", state["shared_context"])
        finally:
            tempdir.cleanup()

    def test_new_project_web_profile_contains_parallel_stage_marker(self):
        exit_code, output, tempdir = self._run_cli("build a kratos web service from scratch")
        try:
            self.assertEqual(exit_code, 0, output)
            self.assertIn("profile=go-kratos-web", output)
            state = self._load_runtime_state(Path(tempdir.name))
            stages = state["shared_context"]["execution_stages"]
            parallel_stages = [stage for stage in stages if stage["parallel"]]
            self.assertEqual(len(parallel_stages), 1)
            self.assertEqual(parallel_stages[0]["roles"], ["backend-dev", "frontend-dev"])
        finally:
            tempdir.cleanup()


if __name__ == "__main__":
    unittest.main()
