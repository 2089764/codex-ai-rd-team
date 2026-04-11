from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import Any

from orchestrator.agent_dispatcher import AgentDispatcher
from orchestrator.coordinator import Coordinator
from orchestrator.planner import build_work_queue
from orchestrator.profiles import load_tech_profiles, resolve_tech_profile
from orchestrator.prompts import load_role_prompts, render_role_prompt
from orchestrator.runtime_models import RuntimeState
from orchestrator.runtime_store import RuntimeStore

try:  # optional runtime dependency in this sandbox
    import typer
except ModuleNotFoundError:  # pragma: no cover
    typer = None


class EchoAgentClient:
    def run(self, *, role: str, prompt: str, context: dict[str, Any]) -> str:
        _ = context
        tail = prompt.splitlines()[-1] if prompt else ""
        return f"[{role}] {tail}".strip()


def _build_prompt_renderer(prompts: dict[str, str]):
    def renderer(item, state) -> str:
        return render_role_prompt(
            role=item.role,
            objective=state.objective,
            instructions=item.instructions,
            profile_name=state.profile_name,
            prompts=prompts,
        )

    return renderer


def run_orchestration(*, objective: str, profile: str | None, runtime_dir: str) -> int:
    catalog = load_tech_profiles()
    resolved = resolve_tech_profile(catalog, explicit=profile, text=objective)
    queue = build_work_queue(profile=resolved, objective=objective)

    run_id = dt.datetime.now(dt.UTC).strftime("run-%Y%m%d%H%M%S")
    state = RuntimeState(
        run_id=run_id,
        profile_name=resolved.name,
        objective=objective,
        queue=queue,
        shared_context={
            "resolved_stack": resolved.data.get("resolved_stack", {}),
        },
    )

    prompts = load_role_prompts()
    dispatcher = AgentDispatcher(
        client=EchoAgentClient(),
        prompt_renderer=_build_prompt_renderer(prompts),
    )
    store = RuntimeStore(Path(runtime_dir))
    coordinator = Coordinator(
        dispatcher=dispatcher,
        store=store,
        has_frontend=bool(resolved.data.get("has_frontend", False)),
    )

    final_state = coordinator.run(state)
    print(
        f"run_id={final_state.run_id} profile={final_state.profile_name} "
        f"status={final_state.status.value} steps={final_state.step_cursor}"
    )
    return 0 if final_state.status.value == "completed" else 1


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codex-ai-rd-team")
    subparsers = parser.add_subparsers(dest="command")

    orchestrate = subparsers.add_parser("orchestrate", help="run coordinator loop")
    orchestrate.add_argument("--objective", required=True, help="project objective text")
    orchestrate.add_argument("--profile", required=False, default=None, help="explicit profile")
    orchestrate.add_argument(
        "--runtime-dir",
        required=False,
        default=str(Path(__file__).resolve().parents[1] / "runtime"),
        help="runtime state directory",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    if args.command != "orchestrate":
        parser.print_help()
        return 1

    try:
        return run_orchestration(
            objective=args.objective,
            profile=args.profile,
            runtime_dir=args.runtime_dir,
        )
    except Exception as exc:  # pragma: no cover
        print(f"error: {exc}", file=sys.stderr)
        return 2


if typer is not None:  # pragma: no cover
    app = typer.Typer(add_completion=False)

    @app.command("orchestrate")
    def orchestrate_cmd(
        objective: str = typer.Option(..., help="project objective text"),
        profile: str | None = typer.Option(None, help="explicit profile name"),
        runtime_dir: str = typer.Option(
            str(Path(__file__).resolve().parents[1] / "runtime"),
            help="runtime state directory",
        ),
    ):
        code = run_orchestration(objective=objective, profile=profile, runtime_dir=runtime_dir)
        raise typer.Exit(code=code)
else:
    app = None


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
