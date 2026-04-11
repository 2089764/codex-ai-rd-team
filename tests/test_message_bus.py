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


if __name__ == "__main__":
    unittest.main()
