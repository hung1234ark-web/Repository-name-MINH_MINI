from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Goal:
    """Mục tiêu hiện tại của MINH MINI."""

    text: str = ""
    intent: str = ""
    action: str = ""
    target: str = ""
    topic: str = ""
    query: str = ""

    status: str = "active"
    priority: str = "normal"

    steps: list[str] = field(default_factory=list)
    current_step: int = 0

    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def completed(self) -> bool:
        return self.status == "completed"

    @property
    def failed(self) -> bool:
        return self.status == "failed"

    @property
    def has_steps(self) -> bool:
        return bool(self.steps)

    @property
    def current_step_text(self) -> str:
        if not self.steps:
            return ""

        if self.current_step < 0:
            return self.steps[0]

        if self.current_step >= len(self.steps):
            return self.steps[-1]

        return self.steps[self.current_step]

    def advance(self) -> bool:
        """Chuyển sang bước tiếp theo."""

        if not self.steps:
            self.status = "completed"
            return True

        if self.current_step + 1 >= len(self.steps):
            self.current_step = len(self.steps)
            self.status = "completed"
            return True

        self.current_step += 1
        return True

    def fail(self, reason: str = "") -> None:
        self.status = "failed"

        if reason:
            self.metadata["failure_reason"] = reason

    def reset(self) -> None:
        self.status = "active"
        self.current_step = 0
        self.metadata.pop("failure_reason", None)

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "intent": self.intent,
            "action": self.action,
            "target": self.target,
            "topic": self.topic,
            "query": self.query,
            "status": self.status,
            "priority": self.priority,
            "steps": list(self.steps),
            "current_step": self.current_step,
            "current_step_text": self.current_step_text,
            "metadata": dict(self.metadata),
        }


class GoalManager:
    """
    P2 - Goal Manager.

    Nhiệm vụ:
    1. Nhận BrainDecision.
    2. Chuyển decision thành Goal có cấu trúc.
    3. Giữ mục tiêu hiện tại.
    4. Theo dõi trạng thái mục tiêu.
    5. Cho phép hoàn thành/thất bại/chuyển bước.

    Goal Manager KHÔNG:
    - tự thực thi tool
    - tự gọi Ollama
    - tự tìm web
    - tự quyết định hành động nguy hiểm
    """

    VERSION = "P2-1.0"

    def __init__(self) -> None:
        self.current_goal: Goal | None = None
        self.goal_history: list[Goal] = []

    # --------------------------------------------------
    # BASIC HELPERS
    # --------------------------------------------------

    @staticmethod
    def _value(
        decision: Any,
        name: str,
        default: Any = "",
    ) -> Any:
        if decision is None:
            return default

        if isinstance(decision, dict):
            return decision.get(name, default)

        return getattr(decision, name, default)

    @staticmethod
    def _clean(value: Any) -> str:
        if value is None:
            return ""

        return str(value).strip()

    # --------------------------------------------------
    # CREATE GOAL
    # --------------------------------------------------

    def create_goal(
        self,
        message: str = "",
        decision: Any = None,
    ) -> Goal:
        """Tạo Goal từ BrainDecision."""

        goal = Goal(
            text=self._clean(message),
            intent=self._clean(
                self._value(decision, "intent")
            ),
            action=self._clean(
                self._value(decision, "action")
            ),
            target=self._clean(
                self._value(decision, "target")
            ),
            topic=self._clean(
                self._value(decision, "topic")
            ),
            query=self._clean(
                self._value(decision, "query")
            ),
        )

        self.current_goal = goal

        return goal

    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------

    def update_from_decision(
        self,
        message: str = "",
        decision: Any = None,
    ) -> Goal:
        """
        Tạo mục tiêu mới hoặc cập nhật mục tiêu hiện tại.

        Giai đoạn P2 chưa tự suy luận mục tiêu phức tạp.
        Brain vẫn là nguồn xác định intent.
        """

        if self.current_goal is None:
            return self.create_goal(
                message,
                decision,
            )

        intent = self._clean(
            self._value(decision, "intent")
        )

        action = self._clean(
            self._value(decision, "action")
        )

        target = self._clean(
            self._value(decision, "target")
        )

        topic = self._clean(
            self._value(decision, "topic")
        )

        query = self._clean(
            self._value(decision, "query")
        )

        # Một intent mới rõ ràng → mục tiêu mới.
        if intent and intent != self.current_goal.intent:
            self.goal_history.append(
                self.current_goal
            )

            return self.create_goal(
                message,
                decision,
            )

        # Cùng mục tiêu → cập nhật phần còn thiếu.
        if message:
            self.current_goal.text = self._clean(
                message
            )

        if intent:
            self.current_goal.intent = intent

        if action:
            self.current_goal.action = action

        if target:
            self.current_goal.target = target

        if topic:
            self.current_goal.topic = topic

        if query:
            self.current_goal.query = query

        return self.current_goal

    # --------------------------------------------------
    # STEP MANAGEMENT
    # --------------------------------------------------

    def set_steps(
        self,
        steps: list[str],
    ) -> Goal | None:
        if self.current_goal is None:
            return None

        clean_steps = [
            self._clean(step)
            for step in steps
            if self._clean(step)
        ]

        self.current_goal.steps = clean_steps
        self.current_goal.current_step = 0

        if not clean_steps:
            self.current_goal.status = "active"

        return self.current_goal

    def advance(self) -> Goal | None:
        if self.current_goal is None:
            return None

        self.current_goal.advance()

        return self.current_goal

    def complete(self) -> Goal | None:
        if self.current_goal is None:
            return None

        self.current_goal.status = "completed"

        if self.current_goal.steps:
            self.current_goal.current_step = len(
                self.current_goal.steps
            )

        return self.current_goal

    def fail(
        self,
        reason: str = "",
    ) -> Goal | None:
        if self.current_goal is None:
            return None

        self.current_goal.fail(reason)

        return self.current_goal

    # --------------------------------------------------
    # READ STATE
    # --------------------------------------------------

    def get_current(self) -> Goal | None:
        return self.current_goal

    def get_status(self) -> dict[str, Any]:
        if self.current_goal is None:
            return {
                "active": False,
                "version": self.VERSION,
                "goal": None,
            }

        return {
            "active": (
                self.current_goal.status == "active"
            ),
            "version": self.VERSION,
            "goal": self.current_goal.to_dict(),
        }

    def clear(self) -> None:
        if self.current_goal is not None:
            self.goal_history.append(
                self.current_goal
            )

        self.current_goal = None


def create_goal_manager() -> GoalManager:
    return GoalManager()


__all__ = [
    "Goal",
    "GoalManager",
    "create_goal_manager",
]
