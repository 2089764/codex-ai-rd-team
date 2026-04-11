from __future__ import annotations

from typing import Protocol

from orchestrator.agent_dispatcher import AgentDispatchError
from orchestrator.message_router import route_next_role
from orchestrator.runtime_models import RoutedMessage, RuntimeState
from orchestrator.state_machine import complete_item, fail_item, start_next_item


class DispatcherLike(Protocol):
    def dispatch(self, item, state: RuntimeState) -> str: ...


class StoreLike(Protocol):
    def save(self, state: RuntimeState): ...


class Coordinator:
    def __init__(self, *, dispatcher: DispatcherLike, store: StoreLike, has_frontend: bool):
        self.dispatcher = dispatcher
        self.store = store
        self.has_frontend = has_frontend

    def run(self, state: RuntimeState) -> RuntimeState:
        while True:
            item = start_next_item(state)
            if item is None:
                break

            try:
                result = self.dispatcher.dispatch(item, state)
            except AgentDispatchError as exc:
                fail_item(state, item.item_id, str(exc))
                break

            complete_item(state, item.item_id, result)
            state.step_cursor += 1
            self._append_trace_message(state, item.role.value, item.item_id, result)

        self.store.save(state)
        return state

    def _append_trace_message(
        self,
        state: RuntimeState,
        role_name: str,
        item_id: str,
        content: str,
    ) -> None:
        from orchestrator.runtime_models import Role

        next_role = route_next_role(Role(role_name), has_frontend=self.has_frontend)
        state.messages.append(
            RoutedMessage(
                sender=role_name,
                recipient=next_role.value if next_role else "coordinator",
                kind="result",
                content=content,
                work_item_id=item_id,
            )
        )
