from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from orchestrator.runtime_models import Role


DEFAULT_ROLE_PROMPTS_PATH = Path(__file__).resolve().parents[1] / "config" / "role-prompts.json"


class PromptConfigError(ValueError):
    pass


def load_role_prompts(path: str | Path = DEFAULT_ROLE_PROMPTS_PATH) -> dict[str, str]:
    config_path = Path(path)
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PromptConfigError(f"prompt config not found: {config_path}") from exc
    except json.JSONDecodeError as exc:
        raise PromptConfigError(f"invalid JSON in prompt config: {config_path}") from exc

    if not isinstance(payload, dict):
        raise PromptConfigError("prompt config must be an object")

    prompts: dict[str, str] = {}
    for key, value in payload.items():
        if not isinstance(key, str) or not key.strip():
            raise PromptConfigError("prompt keys must be non-empty strings")
        if not isinstance(value, str) or not value.strip():
            raise PromptConfigError(f"prompt '{key}' must be a non-empty string")
        prompts[key] = value
    return prompts


def render_role_prompt(
    *,
    role: Role,
    objective: str,
    instructions: str,
    profile_name: str,
    prompts: dict[str, str],
    role_focus: Any = None,
) -> str:
    template = prompts.get(role.value)
    if not template:
        raise PromptConfigError(f"missing prompt template for role: {role.value}")

    focus_block = _render_role_focus(role_focus)
    return (
        f"{template}\n\n"
        f"[Context]\n"
        f"Profile: {profile_name}\n"
        f"Objective: {objective}\n"
        f"Task: {instructions}\n"
        f"{focus_block}"
    )


def render_coordinator_prompt(*, objective: str, profile_name: str, prompts: dict[str, str]) -> str:
    template = prompts.get("coordinator")
    if not template:
        raise PromptConfigError("missing prompt template for role: coordinator")

    return (
        f"{template}\n\n"
        f"[Context]\n"
        f"Profile: {profile_name}\n"
        f"Objective: {objective}\n"
    )


def _render_role_focus(role_focus: Any) -> str:
    if role_focus is None:
        return ""
    if isinstance(role_focus, list):
        items = [item for item in role_focus if isinstance(item, str) and item.strip()]
        if not items:
            return ""
        lines = "\n".join(f"- {item}" for item in items)
        return f"RoleFocus.Priorities:\n{lines}\n"
    if not isinstance(role_focus, dict):
        return ""

    sections: list[tuple[str, list[str]]] = []
    for key, label in (
        ("priorities", "RoleFocus.Priorities"),
        ("must_check", "RoleFocus.MustCheck"),
        ("avoid", "RoleFocus.Avoid"),
    ):
        value = role_focus.get(key, [])
        if not isinstance(value, list):
            continue
        items = [item for item in value if isinstance(item, str) and item.strip()]
        if items:
            sections.append((label, items))

    if not sections:
        return ""

    rendered_sections = []
    for label, items in sections:
        rendered_sections.append(f"{label}:\n" + "\n".join(f"- {item}" for item in items))
    return "\n".join(rendered_sections) + "\n"
