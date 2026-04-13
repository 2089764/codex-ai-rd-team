from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class MessageBus:
    def __init__(self, root: str | Path, *, time_fn=None):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.time_fn = time_fn or time.time

    def append(self, role, kind: str, content: str) -> dict[str, Any]:
        event = {
            "role": self._role_name(role),
            "kind": kind,
            "content": content,
            "ts": self.time_fn(),
        }
        path = self._path_for(role)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False))
            f.write("\n")
        return event

    def read(self, role) -> list[dict[str, Any]]:
        path = self._path_for(role)
        if not path.exists():
            return []

        events: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            events.append(json.loads(line))
        return events

    def last_event_at(self, role):
        events = self.read(role)
        if not events:
            return None
        return events[-1].get("ts")

    def _path_for(self, role) -> Path:
        return self.root / f"{self._role_name(role)}.jsonl"

    def _role_name(self, role) -> str:
        return getattr(role, "value", role)
