from __future__ import annotations

import json
from pathlib import Path

from orchestrator.runtime_models import RuntimeState


class RuntimeStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _state_path(self, run_id: str) -> Path:
        return self.root / f"{run_id}.json"

    def save(self, state: RuntimeState) -> Path:
        target = self._state_path(state.run_id)
        temp = target.with_suffix(".json.tmp")
        temp.write_text(
            json.dumps(state.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp.replace(target)
        return target

    def load(self, run_id: str) -> RuntimeState:
        target = self._state_path(run_id)
        payload = json.loads(target.read_text(encoding="utf-8"))
        return RuntimeState.from_dict(payload)

    def exists(self, run_id: str) -> bool:
        return self._state_path(run_id).exists()

    def list_run_ids(self) -> list[str]:
        run_ids = []
        for path in self.root.glob("*.json"):
            if path.name.endswith(".json"):
                run_ids.append(path.stem)
        run_ids.sort()
        return run_ids
