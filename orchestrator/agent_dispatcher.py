from __future__ import annotations

from typing import Protocol

from orchestrator.runtime_models import RuntimeState, WorkItem


class AgentClient(Protocol):
    def run(self, *, role: str, prompt: str, context: dict) -> str: ...


class AgentDispatchError(RuntimeError):
    pass


class PromptRenderer(Protocol):
    def __call__(self, item: WorkItem, state: RuntimeState) -> str: ...


class AgentDispatcher:
    def __init__(self, client: AgentClient, prompt_renderer: PromptRenderer | None = None):
        self.client = client
        self.prompt_renderer = prompt_renderer

    def dispatch(self, item: WorkItem, state: RuntimeState) -> str:
        item.attempts += 1
        prompt = self.prompt_renderer(item, state) if self.prompt_renderer else self._build_prompt(item, state)
        context = {
            "run_id": state.run_id,
            "profile_name": state.profile_name,
            "objective": state.objective,
            "step_cursor": state.step_cursor,
            "shared_context": state.shared_context,
        }
        try:
            return self.client.run(role=item.role.value, prompt=prompt, context=context)
        except Exception as exc:  # pragma: no cover - exact exception depends on provider
            raise AgentDispatchError(f"dispatch failed for {item.item_id}: {exc}") from exc

    @staticmethod
    def _build_prompt(item: WorkItem, state: RuntimeState) -> str:
        return (
            f"[Run {state.run_id}] role={item.role.value}\\n"
            f"Title: {item.title}\\n"
            f"Instructions: {item.instructions}"
        )
