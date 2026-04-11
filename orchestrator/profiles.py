from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_TECH_PROFILES_PATH = Path(__file__).resolve().parents[1] / "config" / "tech-profiles.json"
ALLOWED_ROLE_FOCUS_KEYS = {
    "analyst",
    "architect",
    "backend-dev",
    "frontend-dev",
    "code-reviewer",
    "tester",
}
REQUIRED_RESOLVED_STACK_FIELDS = ("language", "framework", "delivery", "ui")


class ProfileConfigError(ValueError):
    pass


@dataclass(frozen=True)
class TechProfile:
    name: str
    data: dict[str, Any]


def load_tech_profiles(path: str | Path = DEFAULT_TECH_PROFILES_PATH) -> dict[str, dict[str, Any]]:
    catalog_path = Path(path)
    try:
        payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProfileConfigError(f"profile catalog not found: {catalog_path}") from exc
    except json.JSONDecodeError as exc:
        raise ProfileConfigError(f"invalid JSON in profile catalog: {catalog_path}") from exc

    if not isinstance(payload, dict):
        raise ProfileConfigError("tech profile catalog must be a JSON object")

    catalog: dict[str, dict[str, Any]] = {}
    for name, raw_profile in payload.items():
        if not isinstance(name, str) or not name.strip():
            raise ProfileConfigError("profile names must be non-empty strings")
        if not isinstance(raw_profile, dict):
            raise ProfileConfigError(f"profile '{name}' must be a JSON object")
        _validate_profile_shape(name, raw_profile)
        catalog[name] = deepcopy(raw_profile)

    if "generic" not in catalog:
        raise ProfileConfigError("tech profile catalog must define a 'generic' profile")

    _validate_extends_graph(catalog)
    return catalog


def resolve_tech_profile(
    catalog: dict[str, dict[str, Any]],
    *,
    explicit: str | None = None,
    text: str = "",
) -> TechProfile:
    selected_name = _select_profile_name(catalog, explicit=explicit, text=text)
    resolved = _resolve_profile(selected_name, catalog, seen=())
    return TechProfile(name=selected_name, data=resolved)


def _select_profile_name(
    catalog: dict[str, dict[str, Any]],
    *,
    explicit: str | None,
    text: str,
) -> str:
    if explicit is not None:
        if explicit not in catalog:
            raise ProfileConfigError(f"unknown profile '{explicit}'")
        return explicit

    candidate = _match_profile_by_keyword(catalog, text)
    if candidate is not None:
        return candidate

    return "generic"


def _match_profile_by_keyword(catalog: dict[str, dict[str, Any]], text: str) -> str | None:
    if not text:
        return None

    lowered_text = text.lower()
    matches: list[tuple[int, str]] = []

    for name, raw_profile in catalog.items():
        if name == "generic":
            continue
        keywords = raw_profile.get("keywords", [])
        if not keywords:
            continue
        if not isinstance(keywords, list):
            raise ProfileConfigError(f"profile '{name}' keywords must be a list of strings")
        for keyword in keywords:
            if not isinstance(keyword, str):
                raise ProfileConfigError(f"profile '{name}' keywords must be a list of strings")
            if keyword.lower() in lowered_text:
                matches.append((len(keyword), name))

    if not matches:
        return None

    matches.sort(key=lambda item: (-item[0], item[1]))
    return matches[0][1]


def _resolve_profile(
    name: str,
    catalog: dict[str, dict[str, Any]],
    *,
    seen: tuple[str, ...],
) -> dict[str, Any]:
    if name in seen:
        cycle = " -> ".join((*seen, name))
        raise ProfileConfigError(f"cycle detected in profile inheritance: {cycle}")

    raw_profile = catalog[name]
    parent_name = raw_profile.get("extends")
    if parent_name is None:
        merged: dict[str, Any] = {}
    else:
        if not isinstance(parent_name, str) or not parent_name.strip():
            raise ProfileConfigError(f"profile '{name}' extends must be a non-empty string")
        if parent_name not in catalog:
            raise ProfileConfigError(f"profile '{name}' extends unknown profile '{parent_name}'")
        merged = _resolve_profile(parent_name, catalog, seen=(*seen, name))

    child = deepcopy(raw_profile)
    child.pop("extends", None)
    return _deep_merge(merged, child)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if key == "keywords":
            result[key] = _merge_keywords(result.get(key), value)
            continue

        if key == "role_focus":
            result[key] = _merge_role_focus(result.get(key), value)
            continue

        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def _merge_keywords(parent: Any, child: Any) -> list[str]:
    if parent is None:
        parent_keywords: list[str] = []
    elif isinstance(parent, list):
        parent_keywords = parent
    else:
        raise ProfileConfigError("keywords must be a list of strings")

    if child is None:
        return list(parent_keywords)
    if not isinstance(child, list):
        raise ProfileConfigError("keywords must be a list of strings")

    merged: list[str] = []
    for keyword in [*parent_keywords, *child]:
        if not isinstance(keyword, str):
            raise ProfileConfigError("keywords must be a list of strings")
        if keyword not in merged:
            merged.append(keyword)
    return merged


def _merge_role_focus(parent: Any, child: Any) -> dict[str, list[str]]:
    if parent is None:
        parent_focus: dict[str, list[str]] = {}
    elif isinstance(parent, dict):
        parent_focus = _validate_role_focus_value("role_focus", parent, required=False)
    else:
        raise ProfileConfigError("role_focus must be an object")

    if child is None:
        return deepcopy(parent_focus)
    if not isinstance(child, dict):
        raise ProfileConfigError("role_focus must be an object")

    child_focus = _validate_role_focus_value("role_focus", child, required=False)
    merged: dict[str, list[str]] = deepcopy(parent_focus)
    for key, values in child_focus.items():
        merged[key] = _merge_string_lists(merged.get(key, []), values)
    return merged


def _merge_string_lists(parent: list[str], child: list[str]) -> list[str]:
    merged: list[str] = []
    for item in [*parent, *child]:
        if item not in merged:
            merged.append(item)
    return merged


def _validate_profile_shape(name: str, profile: dict[str, Any]) -> None:
    is_base_profile = "extends" not in profile

    if "extends" in profile and not isinstance(profile["extends"], str):
        raise ProfileConfigError(f"profile '{name}' extends must be a string")

    if is_base_profile and "has_frontend" not in profile:
        raise ProfileConfigError(f"profile '{name}' must define has_frontend")
    if "has_frontend" in profile and not isinstance(profile["has_frontend"], bool):
        raise ProfileConfigError(f"profile '{name}' has_frontend must be a bool")

    if is_base_profile:
        if "resolved_stack" not in profile:
            raise ProfileConfigError(f"profile '{name}' must define resolved_stack")
        if "role_focus" not in profile:
            raise ProfileConfigError(f"profile '{name}' must define role_focus")
        if "keywords" not in profile:
            raise ProfileConfigError(f"profile '{name}' must define keywords")

    if "resolved_stack" in profile:
        _validate_resolved_stack_value(
            name,
            profile["resolved_stack"],
            required=is_base_profile,
        )

    if "role_focus" in profile:
        _validate_role_focus_value(
            name,
            profile["role_focus"],
            required=is_base_profile,
        )

    if "keywords" in profile:
        if not isinstance(profile["keywords"], list) or any(
            not isinstance(item, str) for item in profile["keywords"]
        ):
            raise ProfileConfigError(f"profile '{name}' keywords must be a list of strings")


def _validate_resolved_stack_value(
    name: str,
    value: Any,
    *,
    required: bool,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProfileConfigError(f"profile '{name}' resolved_stack must be an object")

    missing = [field for field in REQUIRED_RESOLVED_STACK_FIELDS if field not in value]
    if required and missing:
        joined = ", ".join(missing)
        raise ProfileConfigError(
            f"profile '{name}' resolved_stack must define: {joined}"
        )

    for field in REQUIRED_RESOLVED_STACK_FIELDS:
        if field in value and not isinstance(value[field], str):
            raise ProfileConfigError(
                f"profile '{name}' resolved_stack.{field} must be a string"
            )

    if "runtime" in value and not isinstance(value["runtime"], dict):
        raise ProfileConfigError(f"profile '{name}' resolved_stack.runtime must be an object")
    return value


def _validate_role_focus_value(
    name: str,
    value: Any,
    *,
    required: bool,
) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        raise ProfileConfigError(f"profile '{name}' role_focus must be an object")

    validated: dict[str, list[str]] = {}
    for key, items in value.items():
        if not isinstance(key, str) or not key.strip():
            raise ProfileConfigError(f"profile '{name}' role_focus keys must be non-empty strings")
        if key not in ALLOWED_ROLE_FOCUS_KEYS:
            raise ProfileConfigError(
                f"profile '{name}' role_focus key '{key}' is not one of the allowed roles"
            )
        if not isinstance(items, list) or any(not isinstance(item, str) for item in items):
            raise ProfileConfigError(
                f"profile '{name}' role_focus values must be lists of strings"
            )
        validated[key] = list(items)
    if required and not validated:
        raise ProfileConfigError(f"profile '{name}' must define at least one role_focus entry")
    return validated


def _validate_extends_graph(catalog: dict[str, dict[str, Any]]) -> None:
    def visit(name: str, path: tuple[str, ...]) -> None:
        if name in path:
            cycle = " -> ".join((*path, name))
            raise ProfileConfigError(f"cycle detected in profile inheritance: {cycle}")

        parent_name = catalog[name].get("extends")
        if parent_name is None:
            return
        if parent_name not in catalog:
            raise ProfileConfigError(f"profile '{name}' extends unknown profile '{parent_name}'")
        visit(parent_name, (*path, name))

    for name in catalog:
        visit(name, ())
