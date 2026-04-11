from __future__ import annotations


def build_role_flow(*, mode: str, has_frontend: bool) -> list[str]:
    if mode == "bugfix":
        return ["backend-dev", "code-reviewer", "tester"]

    if mode == "refactor":
        flow = ["architect", "backend-dev"]
    else:
        flow = ["analyst", "architect", "backend-dev"]

    if has_frontend:
        flow.append("frontend-dev")

    return [*flow, "code-reviewer", "tester"]
