import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from orchestrator.cli import main


class CliE2ETests(unittest.TestCase):
    def test_orchestrate_command_runs_end_to_end(self):
        with tempfile.TemporaryDirectory() as tempdir:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "orchestrate",
                    "--objective",
                    "build a kratos api service",
                    "--runtime-dir",
                    tempdir,
                    "--agent-client",
                    "echo",
                ]
            )

            output = buffer.getvalue()
            self.assertEqual(exit_code, 0, output)
            self.assertIn("status=completed", output.lower())
            self.assertIn("profile=go-kratos-api", output)
            self.assertIn("attempts=", output)
            self.assertIn("feedback_retries=", output)
            self.assertIn("retried_items=", output)

            files = list(Path(tempdir).glob("*.json"))
            self.assertTrue(files)
            self.assertEqual(len(files), 1)

            state = json.loads(files[0].read_text(encoding="utf-8"))
            run_id = state["run_id"]
            artifact_root = Path(tempdir) / "artifacts" / run_id

            self.assertTrue((artifact_root / "requirements/prd.md").exists())
            self.assertTrue((artifact_root / "design/architecture.md").exists())
            self.assertTrue((artifact_root / "design/api-contracts.md").exists())
            self.assertTrue((artifact_root / "reviews/review-1.md").exists())


if __name__ == "__main__":
    unittest.main()
