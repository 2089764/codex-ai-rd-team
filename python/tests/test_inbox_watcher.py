import json
import tempfile
import unittest
from pathlib import Path

from orchestrator.inbox_watcher import read_new_events, team_inbox_path, watch_team_inbox


class InboxWatcherTests(unittest.TestCase):
    def test_team_inbox_path(self):
        path = team_inbox_path(runtime_dir="/tmp/runtime", run_id="run-1", recipient="main")
        self.assertEqual(path.as_posix(), "/tmp/runtime/teams/run-1/inboxes/main.jsonl")

    def test_read_new_events_incremental(self):
        with tempfile.TemporaryDirectory() as tempdir:
            inbox = Path(tempdir) / "main.jsonl"
            inbox.write_text(
                "\n".join(
                    [
                        json.dumps({"kind": "heartbeat", "content": "h1"}, ensure_ascii=False),
                        json.dumps({"kind": "result", "content": "r1"}, ensure_ascii=False),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            first, cursor = read_new_events(inbox, 0)
            self.assertEqual(len(first), 2)
            self.assertEqual(cursor, 2)

            second, cursor2 = read_new_events(inbox, cursor)
            self.assertEqual(second, [])
            self.assertEqual(cursor2, 2)

    def test_watch_team_inbox_prints_events(self):
        with tempfile.TemporaryDirectory() as tempdir:
            runtime = Path(tempdir)
            inbox = runtime / "teams" / "run-1" / "inboxes" / "main.jsonl"
            inbox.parent.mkdir(parents=True, exist_ok=True)
            inbox.write_text(
                json.dumps({"kind": "result", "content": "DONE: ok"}, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            lines: list[str] = []
            code = watch_team_inbox(
                runtime_dir=runtime,
                run_id="run-1",
                max_polls=1,
                interval_sec=0,
                printer=lines.append,
            )

            self.assertEqual(code, 0)
            self.assertTrue(lines[0].startswith("watching inbox:"))
            self.assertIn('"kind": "result"', lines[1])
            self.assertIn('"DONE: ok"', lines[1])

    def test_watch_team_inbox_from_end_skips_history(self):
        with tempfile.TemporaryDirectory() as tempdir:
            runtime = Path(tempdir)
            inbox = runtime / "teams" / "run-2" / "inboxes" / "main.jsonl"
            inbox.parent.mkdir(parents=True, exist_ok=True)
            inbox.write_text(
                json.dumps({"kind": "result", "content": "DONE: old"}, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            lines: list[str] = []
            code = watch_team_inbox(
                runtime_dir=runtime,
                run_id="run-2",
                max_polls=1,
                interval_sec=0,
                from_end=True,
                printer=lines.append,
            )

            self.assertEqual(code, 0)
            self.assertEqual(len(lines), 1)
            self.assertTrue(lines[0].startswith("watching inbox:"))


if __name__ == "__main__":
    unittest.main()
