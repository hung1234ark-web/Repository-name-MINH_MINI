"""
MINH MINI
META-ORCHESTRATOR CORE
P4-1.0

Vai trò:
- Nhận kết quả từ BRAIN / GOAL MANAGER / THINK X.
- Chọn hướng xử lý tiếp theo.
- Không trực tiếp thực thi tool.
- Không gọi Web / Ollama / Action.
- Không thay đổi dữ liệu đầu vào.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


VERSION = "P4-1.0"


@dataclass
class OrchestrationDecision:
    """Kết quả điều phối của Meta-Orchestrator."""

    message: str = ""
    intent: str = ""
    goal: str = ""
    action: str = ""
    target: str = ""
    topic: str = ""

    mode: str = "chat"
    next_step: str = "chat"

    tool: str = ""
    priority: str = "normal"

    reasons: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    plan: List[str] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message": self.message,
            "intent": self.intent,
            "goal": self.goal,
            "action": self.action,
            "target": self.target,
            "topic": self.topic,
            "mode": self.mode,
            "next_step": self.next_step,
            "tool": self.tool,
            "priority": self.priority,
            "reasons": list(self.reasons),
            "constraints": list(self.constraints),
            "plan": list(self.plan),
            "metadata": dict(self.metadata),
        }


class MetaOrchestrator:
    """
    Bộ điều phối trung tâm P4.

    Nguyên tắc:
    1. Không tự thực thi.
    2. Không bỏ qua clarification.
    3. Ưu tiên dữ liệu từ THINK X khi có.
    4. Giữ quyết định đơn giản và dễ kiểm tra.
    """

    VERSION = VERSION

    def __init__(self):
        self.last_decision = None

    # ========================================================
    # SAFE VALUE
    # ========================================================

    @staticmethod
    def _value(obj: Any, name: str, default: Any = "") -> Any:
        if obj is None:
            return default

        if isinstance(obj, dict):
            return obj.get(name, default)

        return getattr(obj, name, default)

    @classmethod
    def _clean(cls, value: Any) -> str:
        if value is None:
            return ""

        return str(value).strip()

    @staticmethod
    def _unique(items: List[str]) -> List[str]:
        result = []

        for item in items:
            if not item:
                continue

            if item not in result:
                result.append(item)

        return result

    # ========================================================
    # INPUT EXTRACTION
    # ========================================================

    def _extract_inputs(
        self,
        message: str,
        brain: Any = None,
        think_x: Any = None,
        goal: Any = None,
    ) -> Dict[str, Any]:

        intent = self._clean(
            self._value(
                think_x,
                "intent",
                self._value(brain, "intent", ""),
            )
        )

        action = self._clean(
            self._value(
                think_x,
                "action",
                self._value(brain, "action", ""),
            )
        )

        target = self._clean(
            self._value(
                think_x,
                "target",
                self._value(brain, "target", ""),
            )
        )

        topic = self._clean(
            self._value(
                think_x,
                "topic",
                self._value(brain, "topic", ""),
            )
        )

        query = self._clean(
            self._value(
                think_x,
                "query",
                self._value(brain, "query", message),
            )
        )

        goal_text = self._clean(
            self._value(
                goal,
                "text",
                self._value(
                    think_x,
                    "goal",
                    message,
                ),
            )
        )

        missing = self._value(
            think_x,
            "missing",
            self._value(brain, "missing", []),
        )

        if not isinstance(missing, list):
            missing = [str(missing)] if missing else []

        risks = self._value(
            think_x,
            "risks",
            [],
        )

        if not isinstance(risks, list):
            risks = [str(risks)] if risks else []

        requires_clarification = bool(
            self._value(
                think_x,
                "requires_clarification",
                self._value(
                    brain,
                    "needs_clarification",
                    False,
                ),
            )
        )

        recommended_tool = self._clean(
            self._value(
                think_x,
                "recommended_tool",
                self._value(brain, "tool", ""),
            )
        )

        plan = self._value(
            think_x,
            "plan",
            [],
        )

        if not isinstance(plan, list):
            plan = [str(plan)] if plan else []

        return {
            "message": self._clean(message),
            "intent": intent,
            "action": action,
            "target": target,
            "topic": topic,
            "query": query,
            "goal": goal_text,
            "missing": missing,
            "risks": risks,
            "requires_clarification": requires_clarification,
            "recommended_tool": recommended_tool,
            "plan": plan,
        }

    # ========================================================
    # PRIORITY
    # ========================================================

    def _priority(
        self,
        intent: str,
        risks: List[str],
    ) -> str:

        if "high_impact_action" in risks:
            return "high"

        if intent in {
            "action",
            "web",
            "memory",
        }:
            return "normal"

        return "normal"

    # ========================================================
    # MODE
    # ========================================================

    def _choose_mode(
        self,
        intent: str,
        requires_clarification: bool,
        missing: List[str],
        plan: List[str],
    ) -> str:

        if requires_clarification or missing:
            return "clarify"

        if intent in {
            "action",
            "web",
            "memory",
            "time",
            "date",
        }:
            return "execute"

        if intent in {
            "follow_up",
            "unknown",
        }:
            return "plan"

        if plan:
            return "plan"

        return "chat"

    # ========================================================
    # NEXT STEP
    # ========================================================

    def _choose_next_step(
        self,
        mode: str,
        recommended_tool: str,
        intent: str,
    ) -> str:

        if mode == "clarify":
            return "clarify"

        if mode == "execute":
            if recommended_tool:
                return "delegate"

            if intent in {
                "action",
                "web",
                "memory",
                "time",
                "date",
            }:
                return "execute"

            return "chat"

        if mode == "plan":
            return "plan"

        return "chat"

    # ========================================================
    # REASONS
    # ========================================================

    def _build_reasons(
        self,
        intent: str,
        mode: str,
        next_step: str,
        missing: List[str],
        risks: List[str],
    ) -> List[str]:

        reasons = []

        if intent:
            reasons.append(
                f"intent={intent}"
            )

        if mode:
            reasons.append(
                f"mode={mode}"
            )

        if next_step:
            reasons.append(
                f"next_step={next_step}"
            )

        if missing:
            reasons.append(
                "missing=" + ",".join(missing)
            )

        if risks:
            reasons.append(
                "risks=" + ",".join(risks)
            )

        return self._unique(reasons)

    # ========================================================
    # MAIN ORCHESTRATION
    # ========================================================

    def orchestrate(
        self,
        message: str,
        brain: Any = None,
        think_x: Any = None,
        goal: Any = None,
    ) -> OrchestrationDecision:

        data = self._extract_inputs(
            message,
            brain,
            think_x,
            goal,
        )

        mode = self._choose_mode(
            data["intent"],
            data["requires_clarification"],
            data["missing"],
            data["plan"],
        )

        next_step = self._choose_next_step(
            mode,
            data["recommended_tool"],
            data["intent"],
        )

        priority = self._priority(
            data["intent"],
            data["risks"],
        )

        reasons = self._build_reasons(
            data["intent"],
            mode,
            next_step,
            data["missing"],
            data["risks"],
        )

        constraints = []

        if data["requires_clarification"]:
            constraints.append(
                "clarification_required"
            )

        if data["missing"]:
            constraints.append(
                "missing_information"
            )

        if "high_impact_action" in data["risks"]:
            constraints.append(
                "high_impact_action_requires_verification"
            )

        decision = OrchestrationDecision(
            message=data["message"],
            intent=data["intent"],
            goal=data["goal"],
            action=data["action"],
            target=data["target"],
            topic=data["topic"],
            mode=mode,
            next_step=next_step,
            tool=data["recommended_tool"],
            priority=priority,
            reasons=reasons,
            constraints=self._unique(constraints),
            plan=list(data["plan"]),
            metadata={
                "version": self.VERSION,
                "risk_count": len(data["risks"]),
                "missing_count": len(data["missing"]),
            },
        )

        self.last_decision = decision

        return decision


def create_meta_orchestrator() -> MetaOrchestrator:
    return MetaOrchestrator()


__all__ = [
    "VERSION",
    "OrchestrationDecision",
    "MetaOrchestrator",
    "create_meta_orchestrator",
]
