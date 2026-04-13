from __future__ import annotations

from orchestrator.profiles import TechProfile
from orchestrator.runtime_models import Role, WorkItem


ROLE_ORDER = (
    Role.ANALYST,
    Role.ARCHITECT,
    Role.BACKEND_DEV,
    Role.FRONTEND_DEV,
    Role.TESTER,
    Role.CODE_REVIEWER,
)


def build_work_queue(*, profile: TechProfile, objective: str) -> list[WorkItem]:
    role_focus = profile.data.get("role_focus", {})
    has_frontend = bool(profile.data.get("has_frontend", False))

    queue: list[WorkItem] = []
    index = 1
    for role in ROLE_ORDER:
        if role == Role.FRONTEND_DEV and not has_frontend:
            continue

        focuses = _extract_focuses(role_focus.get(role.value, []))

        for focus in focuses:
            item_id = f"w{index:03d}"
            queue.append(
                WorkItem(
                    item_id=item_id,
                    role=role,
                    title=f"{role.value}:{focus}",
                    instructions=f"Objective: {objective}; Focus: {focus}",
                )
            )
            index += 1

    return queue


def _extract_focuses(raw_focus) -> list[str]:
    if isinstance(raw_focus, list):
        return [item for item in raw_focus if isinstance(item, str)]

    if isinstance(raw_focus, dict):
        priorities = raw_focus.get("priorities", [])
        must_check = raw_focus.get("must_check", [])
        source = priorities if isinstance(priorities, list) and priorities else must_check
        if not isinstance(source, list):
            return []
        return [item for item in source if isinstance(item, str)]

    return []
