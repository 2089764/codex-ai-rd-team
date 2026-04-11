from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Role(str, Enum):
    ANALYST = "analyst"
    ARCHITECT = "architect"
    BACKEND_DEV = "backend-dev"
    FRONTEND_DEV = "frontend-dev"
    CODE_REVIEWER = "code-reviewer"
    TESTER = "tester"


class WorkStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class OrchestrationStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkItem:
    item_id: str
    role: Role
    title: str
    instructions: str
    status: WorkStatus = WorkStatus.PENDING
    result: str | None = None
    error: str | None = None
    attempts: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "role": self.role.value,
            "title": self.title,
            "instructions": self.instructions,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "attempts": self.attempts,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> WorkItem:
        return cls(
            item_id=str(payload["item_id"]),
            role=Role(payload["role"]),
            title=str(payload["title"]),
            instructions=str(payload["instructions"]),
            status=WorkStatus(payload.get("status", WorkStatus.PENDING.value)),
            result=payload.get("result"),
            error=payload.get("error"),
            attempts=int(payload.get("attempts", 0)),
        )


@dataclass
class RoutedMessage:
    sender: str
    recipient: str
    kind: str
    content: str
    work_item_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "kind": self.kind,
            "content": self.content,
            "work_item_id": self.work_item_id,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RoutedMessage:
        return cls(
            sender=str(payload["sender"]),
            recipient=str(payload["recipient"]),
            kind=str(payload["kind"]),
            content=str(payload["content"]),
            work_item_id=payload.get("work_item_id"),
        )


@dataclass
class RuntimeState:
    run_id: str
    profile_name: str
    objective: str
    status: OrchestrationStatus = OrchestrationStatus.IDLE
    queue: list[WorkItem] = field(default_factory=list)
    messages: list[RoutedMessage] = field(default_factory=list)
    shared_context: dict[str, Any] = field(default_factory=dict)
    step_cursor: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "profile_name": self.profile_name,
            "objective": self.objective,
            "status": self.status.value,
            "queue": [item.to_dict() for item in self.queue],
            "messages": [msg.to_dict() for msg in self.messages],
            "shared_context": self.shared_context,
            "step_cursor": self.step_cursor,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RuntimeState:
        return cls(
            run_id=str(payload["run_id"]),
            profile_name=str(payload["profile_name"]),
            objective=str(payload["objective"]),
            status=OrchestrationStatus(payload.get("status", OrchestrationStatus.IDLE.value)),
            queue=[WorkItem.from_dict(item) for item in payload.get("queue", [])],
            messages=[RoutedMessage.from_dict(msg) for msg in payload.get("messages", [])],
            shared_context=dict(payload.get("shared_context", {})),
            step_cursor=int(payload.get("step_cursor", 0)),
        )

    def next_pending_item(self) -> WorkItem | None:
        for item in self.queue:
            if item.status == WorkStatus.PENDING:
                return item
        return None

    def mark_terminal_if_done(self) -> bool:
        if not self.queue:
            return False
        if any(item.status != WorkStatus.COMPLETED for item in self.queue):
            return False
        if self.status == OrchestrationStatus.COMPLETED:
            return False

        self.status = OrchestrationStatus.COMPLETED
        return True
