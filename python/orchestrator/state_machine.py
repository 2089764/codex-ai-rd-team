from __future__ import annotations

from orchestrator.runtime_models import (
    OrchestrationStatus,
    RuntimeState,
    WorkItem,
    WorkStatus,
)


class StateTransitionError(ValueError):
    pass


_ALLOWED_WORK_TRANSITIONS: dict[WorkStatus, set[WorkStatus]] = {
    WorkStatus.PENDING: {WorkStatus.IN_PROGRESS},
    WorkStatus.IN_PROGRESS: {WorkStatus.COMPLETED, WorkStatus.FAILED},
    WorkStatus.COMPLETED: set(),
    WorkStatus.FAILED: {WorkStatus.IN_PROGRESS},
}


def start_next_item(state: RuntimeState) -> WorkItem | None:
    for item in state.queue:
        if item.status == WorkStatus.PENDING:
            _transition_item(item, WorkStatus.IN_PROGRESS)
            state.status = OrchestrationStatus.RUNNING
            return item
    return None


def complete_item(state: RuntimeState, item_id: str, result: str) -> WorkItem:
    item = _find_item(state, item_id)
    _transition_item(item, WorkStatus.COMPLETED)
    item.result = result
    state.mark_terminal_if_done()
    return item


def fail_item(state: RuntimeState, item_id: str, error: str) -> WorkItem:
    item = _find_item(state, item_id)
    _transition_item(item, WorkStatus.FAILED)
    item.error = error
    state.status = OrchestrationStatus.FAILED
    return item


def _find_item(state: RuntimeState, item_id: str) -> WorkItem:
    for item in state.queue:
        if item.item_id == item_id:
            return item
    raise StateTransitionError(f"work item not found: {item_id}")


def _transition_item(item: WorkItem, target: WorkStatus) -> None:
    allowed = _ALLOWED_WORK_TRANSITIONS[item.status]
    if target not in allowed:
        raise StateTransitionError(
            f"invalid work status transition: {item.status.value} -> {target.value}"
        )
    item.status = target
