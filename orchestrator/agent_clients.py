from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any


class EchoAgentClient:
    def run(self, *, role: str, prompt: str, context: dict[str, Any]) -> str:
        _ = context
        tail = prompt.splitlines()[-1] if prompt else ""
        return f"[{role}] {tail}".strip()


class CodexAgentClient:
    def __init__(
        self,
        *,
        binary: str = "codex",
        model: str | None = None,
        workdir: str | Path | None = None,
        timeout_sec: float = 600.0,
    ):
        self.binary = binary
        self.model = model
        self.workdir = str(Path(workdir)) if workdir is not None else None
        self.timeout_sec = timeout_sec

    def run(self, *, role: str, prompt: str, context: dict[str, Any]) -> str:
        rendered_prompt = self._build_contract_prompt(role=role, prompt=prompt, context=context)
        output_path = self._mktemp_output_path()

        cmd = [self.binary, "exec", "--skip-git-repo-check", "--color", "never"]
        if self.workdir:
            cmd.extend(["-C", self.workdir])
        if self.model:
            cmd.extend(["--model", self.model])
        cmd.extend(["--output-last-message", output_path, "-"])

        try:
            completed = subprocess.run(
                cmd,
                input=rendered_prompt,
                text=True,
                capture_output=True,
                check=False,
                timeout=self.timeout_sec,
            )
        except subprocess.TimeoutExpired as exc:
            self._cleanup_output_file(output_path)
            raise RuntimeError(f"codex exec timeout after {self.timeout_sec}s") from exc

        if completed.returncode != 0:
            self._cleanup_output_file(output_path)
            stderr = (completed.stderr or "").strip()
            stdout = (completed.stdout or "").strip()
            reason = stderr or stdout or f"exit code {completed.returncode}"
            raise RuntimeError(f"codex exec failed: {reason}")

        message = self._read_output_file(output_path).strip()
        self._cleanup_output_file(output_path)
        if not message:
            raise RuntimeError("codex exec returned empty final message")
        return message

    @staticmethod
    def _mktemp_output_path() -> str:
        fd, path = tempfile.mkstemp(prefix="codex-last-message-", suffix=".txt")
        os.close(fd)
        Path(path).unlink(missing_ok=True)
        return path

    @staticmethod
    def _read_output_file(path: str) -> str:
        file_path = Path(path)
        if not file_path.exists():
            return ""
        return file_path.read_text(encoding="utf-8")

    @staticmethod
    def _cleanup_output_file(path: str) -> None:
        Path(path).unlink(missing_ok=True)

    @staticmethod
    def _build_contract_prompt(*, role: str, prompt: str, context: dict[str, Any]) -> str:
        contract = _output_contract_for_role(role)
        context_json = json.dumps(context, ensure_ascii=False, indent=2)
        return (
            "你是 RD 多角色编排中的执行代理。\n"
            f"当前角色: {role}\n\n"
            "上下文(JSON):\n"
            f"{context_json}\n\n"
            "任务说明:\n"
            f"{prompt}\n\n"
            "输出契约(必须遵守):\n"
            f"{contract}\n\n"
            "只输出最终结果，不要输出额外前后缀说明。"
        )


def _output_contract_for_role(role: str) -> str:
    if role == "code-reviewer":
        return "首行必须以 `REJECT:` 或 `APPROVE:` 开头。"
    if role == "tester":
        return "首行必须以 `BUG:`、`FAIL:` 或 `PASS:` 开头。"
    return "首行必须以 `DONE:` 开头。"
