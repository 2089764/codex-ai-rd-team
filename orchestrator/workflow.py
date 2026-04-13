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


def build_execution_stages(*, mode: str, has_frontend: bool) -> list[dict[str, object]]:
    if mode == "bugfix":
        return [
            {"name": "dev", "roles": ["backend-dev"], "parallel": False},
            {"name": "review", "roles": ["code-reviewer"], "parallel": False},
            {"name": "test", "roles": ["tester"], "parallel": False},
        ]

    if mode == "refactor":
        stages: list[dict[str, object]] = [
            {"name": "architecture", "roles": ["architect"], "parallel": False},
        ]
    else:
        stages = [
            {"name": "analysis", "roles": ["analyst"], "parallel": False},
            {"name": "architecture", "roles": ["architect"], "parallel": False},
        ]

    if has_frontend:
        stages.append(
            {
                "name": "development",
                "roles": ["backend-dev", "frontend-dev"],
                "parallel": True,
            }
        )
    else:
        stages.append(
            {
                "name": "development",
                "roles": ["backend-dev"],
                "parallel": False,
            }
        )

    stages.extend(
        [
            {"name": "review", "roles": ["code-reviewer"], "parallel": False},
            {"name": "test", "roles": ["tester"], "parallel": False},
        ]
    )
    return stages
