import json
import tempfile
import unittest
from pathlib import Path

from orchestrator.message_bus import MessageBus


class MessageBusTests(unittest.TestCase):
    def test_append_read_and_last_event_at(self):
        times = iter([1.25, 2.5])

        bus = MessageBus(Path(tempfile.mkdtemp()), time_fn=lambda: next(times))

        bus.append("analyst", "heartbeat", "ping")
        bus.append("analyst", "result", "done")

        events = bus.read("analyst")

        self.assertEqual(
            events,
            [
                {"role": "analyst", "kind": "heartbeat", "content": "ping", "ts": 1.25},
                {"role": "analyst", "kind": "result", "content": "done", "ts": 2.5},
            ],
        )
        self.assertEqual(bus.last_event_at("analyst"), 2.5)
        self.assertIsNone(bus.last_event_at("architect"))

        path = bus.root / "analyst.jsonl"
        self.assertTrue(path.exists())
        self.assertEqual(
            path.read_text(encoding="utf-8").splitlines(),
            [
                json.dumps({"role": "analyst", "kind": "heartbeat", "content": "ping", "ts": 1.25}, ensure_ascii=False),
                json.dumps({"role": "analyst", "kind": "result", "content": "done", "ts": 2.5}, ensure_ascii=False),
            ],
        )

    def test_append_mirrors_event_to_team_inboxes(self):
        root = Path(tempfile.mkdtemp())
        times = iter([10.0])

        bus = MessageBus(
            root / "inboxes",
            team_name="rd-team-1",
            teams_root=root / "teams",
            time_fn=lambda: next(times),
        )

        bus.append("analyst", "heartbeat", "dispatch-start:w1")

        main_inbox = root / "teams" / "rd-team-1" / "inboxes" / "main.jsonl"
        analyst_inbox = root / "teams" / "rd-team-1" / "inboxes" / "analyst.jsonl"

        self.assertTrue(main_inbox.exists())
        self.assertTrue(analyst_inbox.exists())

        main_events = [json.loads(line) for line in main_inbox.read_text(encoding="utf-8").splitlines()]
        analyst_events = [json.loads(line) for line in analyst_inbox.read_text(encoding="utf-8").splitlines()]

        expected = {
            "sender": "analyst",
            "recipient": "main",
            "kind": "heartbeat",
            "summary": "heartbeat",
            "content": "dispatch-start:w1",
            "ts": 10.0,
        }
        self.assertEqual(main_events, [expected])
        self.assertEqual(analyst_events, [expected])

    def test_append_routed_writes_recipient_and_main_inboxes(self):
        root = Path(tempfile.mkdtemp())
        times = iter([11.0])
        bus = MessageBus(
            root / "inboxes",
            team_name="rd-team-2",
            teams_root=root / "teams",
            time_fn=lambda: next(times),
        )

        bus.append_routed(
            sender="analyst",
            recipient="architect",
            kind="message",
            content="请确认接口契约",
            summary="handoff",
            work_item_id="w1",
        )

        architect_inbox = root / "teams" / "rd-team-2" / "inboxes" / "architect.jsonl"
        main_inbox = root / "teams" / "rd-team-2" / "inboxes" / "main.jsonl"
        analyst_inbox = root / "teams" / "rd-team-2" / "inboxes" / "analyst.jsonl"

        expected = {
            "sender": "analyst",
            "recipient": "architect",
            "kind": "message",
            "content": "请确认接口契约",
            "summary": "handoff",
            "work_item_id": "w1",
            "ts": 11.0,
        }

        self.assertEqual(
            [json.loads(line) for line in architect_inbox.read_text(encoding="utf-8").splitlines()],
            [expected],
        )
        self.assertEqual(
            [json.loads(line) for line in main_inbox.read_text(encoding="utf-8").splitlines()],
            [expected],
        )
        self.assertEqual(
            [json.loads(line) for line in analyst_inbox.read_text(encoding="utf-8").splitlines()],
            [expected],
        )


if __name__ == "__main__":
    unittest.main()
