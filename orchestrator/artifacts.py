from __future__ import annotations

from pathlib import Path


class ArtifactWriter:
    def __init__(self, docs_root: str | Path):
        self.docs_root = Path(docs_root)

    def _write(self, relative_path: str, content: str) -> Path:
        path = self.docs_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def write_prd(self, content: str) -> Path:
        return self._write("requirements/prd.md", content)

    def write_architecture(self, content: str) -> Path:
        return self._write("design/architecture.md", content)

    def write_api_contracts(self, content: str) -> Path:
        return self._write("design/api-contracts.md", content)

    def write_review(self, number: int, content: str) -> Path:
        return self._write(f"reviews/review-{number}.md", content)
