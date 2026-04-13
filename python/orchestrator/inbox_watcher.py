from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Callable


def team_inbox_path(*, runtime_dir: str | Path, run_id: str, recipient: str = "main") -> Path:
    return Path(runtime_dir) / "teams" / run_id / "inboxes" / f"{recipient}.jsonl"


def read_new_events(path: str | Path, start_line: int = 0) -> tuple[list[dict], int]:
    inbox_path = Path(path)
    if not inbox_path.exists():
        return [], start_line

    lines = inbox_path.read_text(encoding="utf-8").splitlines()
    if start_line >= len(lines):
        return [], len(lines)

    events: list[dict] = []
    for raw in lines[start_line:]:
        if not raw.strip():
            continue
        events.append(json.loads(raw))
    return events, len(lines)


def watch_team_inbox(
    *,
    runtime_dir: str | Path,
    run_id: str,
    recipient: str = "main",
    interval_sec: float = 30.0,
    max_polls: int | None = None,
    from_end: bool = False,
    printer: Callable[[str], None] = print,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> int:
    path = team_inbox_path(runtime_dir=runtime_dir, run_id=run_id, recipient=recipient)
    line_offset = 0

    if from_end and path.exists():
        line_offset = len(path.read_text(encoding="utf-8").splitlines())

    printer(f"watching inbox: {path} interval={interval_sec}s recipient={recipient}")

    polls = 0
    while True:
        events, line_offset = read_new_events(path, line_offset)
        for event in events:
            printer(json.dumps(event, ensure_ascii=False))

        polls += 1
        if max_polls is not None and polls >= max_polls:
            break

        sleep_fn(interval_sec)

    return 0
