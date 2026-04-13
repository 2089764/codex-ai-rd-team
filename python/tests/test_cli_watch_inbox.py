import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from orchestrator.cli import main


class CliWatchInboxTests(unittest.TestCase):
    def test_watch_inbox_command_reads_main_inbox(self):
        with tempfile.TemporaryDirectory() as tempdir:
            runtime = Path(tempdir)
            run_id = "run-20260414090909000000"
            inbox = runtime / "teams" / run_id / "inboxes" / "main.jsonl"
            inbox.parent.mkdir(parents=True, exist_ok=True)
            inbox.write_text(
                json.dumps({"kind": "result", "content": "DONE: sample"}, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "watch-inbox",
                        "--runtime-dir",
                        tempdir,
                        "--run-id",
                        run_id,
                        "--max-polls",
                        "1",
                        "--interval-sec",
                        "0",
                    ]
                )

            output = buffer.getvalue()
            self.assertEqual(exit_code, 0, output)
            self.assertIn("watching inbox:", output)
            self.assertIn('"DONE: sample"', output)


if __name__ == "__main__":
    unittest.main()
