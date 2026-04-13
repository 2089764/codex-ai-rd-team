from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class MessageBus:
    def __init__(
        self,
        root: str | Path,
        *,
        time_fn=None,
        team_name: str | None = None,
        teams_root: str | Path | None = None,
    ):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.time_fn = time_fn or time.time
        self.team_name = team_name
        self.teams_root = (
            Path(teams_root) if teams_root is not None else self.root.parent / "teams"
        )

    def append(self, role, kind: str, content: str) -> dict[str, Any]:
        sender = self._role_name(role)
        event = {
            "role": sender,
            "kind": kind,
            "content": content,
            "ts": self.time_fn(),
        }
        path = self._path_for(role)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False))
            f.write("\n")

        self._append_team_inbox_event(
            sender=sender,
            recipient="main",
            kind=kind,
            content=content,
            summary=kind,
            ts=event["ts"],
        )
        return event

    def append_routed(
        self,
        *,
        sender: str,
        recipient: str,
        kind: str,
        content: str,
        summary: str | None = None,
        work_item_id: str | None = None,
    ) -> dict[str, Any]:
        ts = self.time_fn()
        payload: dict[str, Any] = {
            "sender": sender,
            "recipient": recipient,
            "kind": kind,
            "content": content,
            "summary": summary if summary is not None else kind,
            "ts": ts,
        }
        if work_item_id is not None:
            payload["work_item_id"] = work_item_id

        self._append_team_inbox_line(recipient=recipient, payload=payload)
        if recipient != "main":
            self._append_team_inbox_line(recipient="main", payload=payload)
        self._append_team_inbox_line(recipient=sender, payload=payload)
        return payload

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

    def _append_team_inbox_event(
        self,
        *,
        sender: str,
        recipient: str,
        kind: str,
        content: str,
        summary: str,
        ts: float,
    ) -> None:
        payload: dict[str, Any] = {
            "sender": sender,
            "recipient": recipient,
            "kind": kind,
            "summary": summary,
            "content": content,
            "ts": ts,
        }
        self._append_team_inbox_line(recipient=recipient, payload=payload)
        self._append_team_inbox_line(recipient=sender, payload=payload)

    def _append_team_inbox_line(self, *, recipient: str, payload: dict[str, Any]) -> None:
        path = self._team_inbox_path_for(recipient)
        if path is None:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False))
            f.write("\n")

    def _team_inbox_path_for(self, recipient: str) -> Path | None:
        if self.team_name is None:
            return None
        return self.teams_root / self.team_name / "inboxes" / f"{recipient}.jsonl"

    def _role_name(self, role) -> str:
        return getattr(role, "value", role)
