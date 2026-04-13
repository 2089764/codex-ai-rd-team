from __future__ import annotations

from orchestrator.runtime_models import Role


def route_next_role(current_role: Role, *, has_frontend: bool) -> Role | None:
    if current_role == Role.ANALYST:
        return Role.ARCHITECT
    if current_role == Role.ARCHITECT:
        return Role.BACKEND_DEV
    if current_role == Role.BACKEND_DEV:
        return Role.FRONTEND_DEV if has_frontend else Role.CODE_REVIEWER
    if current_role == Role.FRONTEND_DEV:
        return Role.CODE_REVIEWER
    if current_role == Role.CODE_REVIEWER:
        return Role.TESTER
    if current_role == Role.TESTER:
        return None
    return None
