from __future__ import annotations

import json
from pathlib import Path

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
) -> str:
    template = prompts.get(role.value)
    if not template:
        raise PromptConfigError(f"missing prompt template for role: {role.value}")

    return (
        f"{template}\n\n"
        f"[Context]\n"
        f"Profile: {profile_name}\n"
        f"Objective: {objective}\n"
        f"Task: {instructions}\n"
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
