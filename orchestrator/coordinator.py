from __future__ import annotations

import time
from pathlib import Path
from typing import Protocol

from orchestrator.artifacts import ArtifactWriter
from orchestrator.agent_dispatcher import AgentDispatchError
from orchestrator.message_router import route_next_role
from orchestrator.runtime_models import (
    OrchestrationStatus,
    RoutedMessage,
    Role,
    RuntimeState,
    WorkItem,
    WorkStatus,
)
from orchestrator.state_machine import complete_item, fail_item, start_next_item


class DispatcherLike(Protocol):
    def dispatch(self, item, state: RuntimeState) -> str: ...


class StoreLike(Protocol):
    def save(self, state: RuntimeState): ...


class MessageBusLike(Protocol):
    def last_event_at(self, role): ...


class Coordinator:
    def __init__(
        self,
        *,
        dispatcher: DispatcherLike,
        store: StoreLike,
        has_frontend: bool,
        artifact_writer: ArtifactWriter | None = None,
        artifact_root: str | Path | None = None,
        message_bus: MessageBusLike | None = None,
        time_fn=None,
        heartbeat_timeout_sec: float = 150.0,
        max_redispatch: int = 2,
    ):
        self.dispatcher = dispatcher
        self.store = store
        self.has_frontend = has_frontend
        self.artifact_writer = artifact_writer
        self.artifact_root = Path(artifact_root) if artifact_root is not None else Path("runtime") / "artifacts"
        self.message_bus = message_bus
        self.time_fn = time_fn or time.time
        self.heartbeat_timeout_sec = heartbeat_timeout_sec
        self.max_redispatch = max_redispatch
        self.feedback_retry_counts: dict[str, int] = {}
        self.review_artifact_counter = 0

    def run(self, state: RuntimeState) -> RuntimeState:
        artifact_writer = self._resolve_artifact_writer(state)
        while True:
            if state.status == OrchestrationStatus.FAILED:
                break

            if self._redispatch_timed_out_items(state):
                if state.status == OrchestrationStatus.FAILED:
                    break

            item = start_next_item(state)
            if item is None:
                break

            try:
                result = self.dispatcher.dispatch(item, state)
            except AgentDispatchError as exc:
                fail_item(state, item.item_id, str(exc))
                break

            retryable_feedback = self._handle_retryable_feedback(state, item, result)
            if not retryable_feedback:
                if item.error is not None:
                    item.error = None
                complete_item(state, item.item_id, result)

            try:
                self._persist_standard_a_artifacts(artifact_writer, state, item, result)
            except Exception:
                pass
            state.step_cursor += 1
            self._append_trace_message(state, item.role.value, item.item_id, result)

            if state.status == OrchestrationStatus.NEEDS_USER_DECISION:
                break

        self.store.save(state)
        return state

    def _resolve_artifact_writer(self, state: RuntimeState) -> ArtifactWriter:
        if self.artifact_writer is not None:
            return self.artifact_writer
        return ArtifactWriter(self.artifact_root / state.run_id)

    def _redispatch_timed_out_items(self, state: RuntimeState) -> bool:
        if self.message_bus is None:
            return False

        now = self.time_fn()
        redispatched = False

        for item in state.queue:
            if item.status != WorkStatus.IN_PROGRESS:
                continue

            last_event_at = self.message_bus.last_event_at(item.role)
            timed_out = last_event_at is None or (now - last_event_at) > self.heartbeat_timeout_sec
            if not timed_out:
                continue

            item.attempts += 1
            item.error = f"heartbeat timeout after {self.heartbeat_timeout_sec}s"
            item.result = None

            if item.attempts > self.max_redispatch:
                item.status = WorkStatus.FAILED
                state.status = OrchestrationStatus.FAILED
                return True

            item.status = WorkStatus.PENDING
            redispatched = True

        return redispatched

    def _handle_retryable_feedback(
        self,
        state: RuntimeState,
        item: WorkItem,
        result: str,
    ) -> bool:
        if not self._is_retryable_feedback(item, result):
            return False

        key = f"{item.item_id}:{item.role.value}"
        retry_count = self.feedback_retry_counts.get(key, 0) + 1
        self.feedback_retry_counts[key] = retry_count
        item.error = result
        item.result = None

        if retry_count > 2:
            item.status = WorkStatus.FAILED
            state.status = OrchestrationStatus.NEEDS_USER_DECISION
        else:
            item.status = WorkStatus.PENDING

        return True

    def _is_retryable_feedback(self, item: WorkItem, result: str) -> bool:
        normalized = result.lstrip()
        if item.role == Role.CODE_REVIEWER:
            return normalized.startswith("REJECT:")
        if item.role == Role.TESTER:
            return normalized.startswith("BUG:") or normalized.startswith("FAIL:")
        return False

    def _persist_standard_a_artifacts(
        self,
        artifact_writer: ArtifactWriter,
        state: RuntimeState,
        item: WorkItem,
        content: str,
    ) -> None:
        role = item.role
        if role == Role.ANALYST:
            artifact_writer.write_prd(content)
        elif role == Role.ARCHITECT:
            artifact_writer.write_architecture(content)
            artifact_writer.write_api_contracts(content)
        elif role == Role.CODE_REVIEWER:
            self.review_artifact_counter += 1
            artifact_writer.write_review(self.review_artifact_counter, content)

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
