from __future__ import annotations

import argparse
import datetime as dt
import os
import shutil
import sys
from pathlib import Path

from orchestrator.agent_dispatcher import AgentDispatcher
from orchestrator.agent_clients import CodexAgentClient, EchoAgentClient
from orchestrator.coordinator import Coordinator
from orchestrator.message_bus import MessageBus
from orchestrator.planner import build_work_queue
from orchestrator.mode_classifier import classify_mode
from orchestrator.profiles import load_tech_profiles, resolve_tech_profile
from orchestrator.prompts import load_role_prompts, render_role_prompt
from orchestrator.runtime_models import OrchestrationStatus, RuntimeState
from orchestrator.runtime_store import RuntimeStore
from orchestrator.workflow import build_execution_stages, build_role_flow

try:  # optional runtime dependency in this sandbox
    import typer
except ModuleNotFoundError:  # pragma: no cover
    typer = None


def _build_prompt_renderer(prompts: dict[str, str]):
    def renderer(item, state) -> str:
        role_focus = None
        role_focus_map = state.shared_context.get("role_focus", {})
        if isinstance(role_focus_map, dict):
            role_focus = role_focus_map.get(item.role.value)
        return render_role_prompt(
            role=item.role,
            objective=state.objective,
            instructions=item.instructions,
            profile_name=state.profile_name,
            prompts=prompts,
            role_focus=role_focus,
        )

    return renderer


def _apply_mode_flow(queue, *, mode: str, has_frontend: bool):
    flow = build_role_flow(mode=mode, has_frontend=has_frontend)
    flow_order = {role_name: index for index, role_name in enumerate(flow)}

    indexed_items = [
        (index, item)
        for index, item in enumerate(queue)
        if item.role.value in flow_order
    ]
    indexed_items.sort(key=lambda pair: (flow_order[pair[1].role.value], pair[0]))
    return [item for _, item in indexed_items]


def _create_agent_client(
    *,
    agent_client: str,
    codex_bin: str,
    codex_model: str | None,
    workdir: str,
):
    resolved_codex_bin = _resolve_executable(codex_bin)

    if agent_client == "echo":
        return EchoAgentClient()
    if agent_client == "codex":
        if not resolved_codex_bin:
            raise RuntimeError(f"codex executable not found: {codex_bin}")
        return CodexAgentClient(binary=resolved_codex_bin, model=codex_model, workdir=workdir)

    # auto
    if resolved_codex_bin:
        return CodexAgentClient(binary=resolved_codex_bin, model=codex_model, workdir=workdir)
    return EchoAgentClient()


def _resolve_executable(binary: str) -> str | None:
    if os.path.sep in binary:
        path = Path(binary)
        return str(path) if path.exists() else None
    return shutil.which(binary)


def run_orchestration(
    *,
    objective: str,
    profile: str | None,
    runtime_dir: str,
    workdir: str | None = None,
    agent_client: str = "auto",
    codex_bin: str = "codex",
    codex_model: str | None = None,
    interactive: bool = False,
) -> int:
    catalog = load_tech_profiles()
    resolved = resolve_tech_profile(catalog, explicit=profile, text=objective)
    mode = classify_mode(objective)
    has_frontend = bool(resolved.data.get("has_frontend", False))
    queue = build_work_queue(profile=resolved, objective=objective)
    queue = _apply_mode_flow(queue, mode=mode, has_frontend=has_frontend)
    execution_stages = build_execution_stages(mode=mode, has_frontend=has_frontend)

    run_id = dt.datetime.now(dt.UTC).strftime("run-%Y%m%d%H%M%S%f")
    state = RuntimeState(
        run_id=run_id,
        profile_name=resolved.name,
        objective=objective,
        queue=queue,
        shared_context={
            "mode": mode,
            "project_type": resolved.name,
            "effective_profile": resolved.name,
            "resolved_stack": resolved.data.get("resolved_stack", {}),
            "role_focus": resolved.data.get("role_focus", {}),
            "execution_stages": execution_stages,
        },
    )

    prompts = load_role_prompts()
    project_root = str(Path(__file__).resolve().parents[1])
    target_workdir = workdir or project_root
    dispatcher = AgentDispatcher(
        client=_create_agent_client(
            agent_client=agent_client,
            codex_bin=codex_bin,
            codex_model=codex_model,
            workdir=target_workdir,
        ),
        prompt_renderer=_build_prompt_renderer(prompts),
    )
    store = RuntimeStore(Path(runtime_dir))
    message_bus = MessageBus(Path(runtime_dir) / "inboxes")
    coordinator = Coordinator(
        dispatcher=dispatcher,
        store=store,
        has_frontend=has_frontend,
        artifact_root=Path(runtime_dir) / "artifacts",
        message_bus=message_bus,
    )

    if interactive:
        final_state = _run_interactive_stages(
            coordinator=coordinator,
            state=state,
            execution_stages=execution_stages,
        )
    else:
        final_state = coordinator.run(state)
    metrics = final_state.shared_context.get("run_metrics", {})
    attempts = metrics.get("total_attempts", 0)
    feedback_retries = metrics.get("feedback_retries", 0)
    retried_items = metrics.get("retried_items", 0)
    print(
        f"run_id={final_state.run_id} mode={mode} profile={final_state.profile_name} "
        f"status={final_state.status.value} steps={final_state.step_cursor} "
        f"attempts={attempts} feedback_retries={feedback_retries} retried_items={retried_items}"
    )
    return 0 if final_state.status.value == "completed" else 1


def _run_interactive_stages(
    *,
    coordinator: Coordinator,
    state: RuntimeState,
    execution_stages: list[dict[str, object]],
) -> RuntimeState:
    final_state = state
    for stage_index, stage in enumerate(execution_stages):
        roles = stage.get("roles", [])
        if not isinstance(roles, list):
            continue
        allowed_roles = {role for role in roles if isinstance(role, str)}
        final_state = coordinator.run(final_state, allowed_roles=allowed_roles)

        if final_state.status in {
            OrchestrationStatus.FAILED,
            OrchestrationStatus.NEEDS_USER_DECISION,
            OrchestrationStatus.COMPLETED,
        }:
            break

        if stage_index >= len(execution_stages) - 1:
            break

        if not _confirm_stage_continue(stage):
            final_state.status = OrchestrationStatus.NEEDS_USER_DECISION
            coordinator.store.save(final_state)
            break

    return final_state


def _confirm_stage_continue(stage: dict[str, object]) -> bool:
    stage_name = str(stage.get("name", "unknown"))
    if stage_name == "analysis":
        prompt = "分析阶段已完成，是否确认继续进入架构阶段？ [y/N]: "
    elif stage_name == "architecture":
        prompt = "架构阶段已完成，是否确认继续进入开发阶段？ [y/N]: "
    else:
        prompt = f"阶段 {stage_name} 已完成，是否继续下一阶段？ [y/N]: "

    answer = input(prompt).strip().lower()
    return answer in {"y", "yes", "是"}


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
    orchestrate.add_argument(
        "--workdir",
        required=False,
        default=None,
        help="target project working directory for codex agent execution",
    )
    orchestrate.add_argument(
        "--agent-client",
        choices=("auto", "codex", "echo"),
        default="auto",
        help="agent client backend",
    )
    orchestrate.add_argument(
        "--codex-bin",
        required=False,
        default="codex",
        help="codex executable path",
    )
    orchestrate.add_argument(
        "--codex-model",
        required=False,
        default=None,
        help="codex model name",
    )
    orchestrate.add_argument(
        "--interactive",
        action="store_true",
        help="enable stage checkpoints with user confirmation",
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
            workdir=args.workdir,
            agent_client=args.agent_client,
            codex_bin=args.codex_bin,
            codex_model=args.codex_model,
            interactive=args.interactive,
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
        workdir: str | None = typer.Option(
            None,
            help="target project working directory for codex agent execution",
        ),
        agent_client: str = typer.Option(
            "auto",
            help="agent client backend: auto/codex/echo",
        ),
        codex_bin: str = typer.Option(
            "codex",
            help="codex executable path",
        ),
        codex_model: str | None = typer.Option(
            None,
            help="codex model name",
        ),
        interactive: bool = typer.Option(
            False,
            help="enable stage checkpoints with user confirmation",
        ),
    ):
        code = run_orchestration(
            objective=objective,
            profile=profile,
            runtime_dir=runtime_dir,
            workdir=workdir,
            agent_client=agent_client,
            codex_bin=codex_bin,
            codex_model=codex_model,
            interactive=interactive,
        )
        raise typer.Exit(code=code)
else:
    app = None


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
