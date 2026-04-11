import io
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
                    ]
                )

            output = buffer.getvalue()
            self.assertEqual(exit_code, 0, output)
            self.assertIn("status=completed", output.lower())
            self.assertIn("profile=go-kratos-api", output)

            files = list(Path(tempdir).glob("*.json"))
            self.assertTrue(files)


if __name__ == "__main__":
    unittest.main()
