"""
MINH MINI - THINK X CORE
P3-1.0

Core planning layer:
- Nhận message / BrainDecision / Goal
- Phân tích mục tiêu
- Phát hiện dữ kiện thiếu
- Đánh giá rủi ro cơ bản
- Xác định độ phức tạp
- Tạo kế hoạch xử lý
- Không thực thi tool
- Không thay đổi main.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


VERSION = "P3-1.0"


# ============================================================
# DATA MODEL
# ============================================================

@dataclass
class ThinkXResult:
    """Kết quả phân tích của THINK X."""

    message: str = ""

    goal: str = ""

    intent: str = ""

    action: str = ""

    target: str = ""

    topic: str = ""

    query: str = ""

    facts: List[str] = field(default_factory=list)

    missing: List[str] = field(default_factory=list)

    risks: List[str] = field(default_factory=list)

    complexity: str = "low"

    requires_clarification: bool = False

    recommended_tool: str = ""

    plan: List[str] = field(default_factory=list)

    reason: str = ""

    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message": self.message,
            "goal": self.goal,
            "intent": self.intent,
            "action": self.action,
            "target": self.target,
            "topic": self.topic,
            "query": self.query,
            "facts": list(self.facts),
            "missing": list(self.missing),
            "risks": list(self.risks),
            "complexity": self.complexity,
            "requires_clarification": self.requires_clarification,
            "recommended_tool": self.recommended_tool,
            "plan": list(self.plan),
            "reason": self.reason,
            "metadata": dict(self.metadata),
        }


# ============================================================
# THINK X CORE
# ============================================================

class ThinkXCore:
    """
    THINK X planning core.

    P3-1 intentionally remains deterministic and lightweight.
    It does not execute actions and does not call Ollama.
    """

    VERSION = VERSION

    def __init__(self) -> None:
        self.version = self.VERSION

    # --------------------------------------------------------
    # Generic helpers
    # --------------------------------------------------------

    @staticmethod
    def _value(obj: Any, name: str, default: Any = "") -> Any:
        if obj is None:
            return default

        if isinstance(obj, dict):
            return obj.get(name, default)

        return getattr(obj, name, default)

    @staticmethod
    def _clean(value: Any) -> str:
        if value is None:
            return ""

        return str(value).strip()

    @staticmethod
    def _unique(items: List[str]) -> List[str]:
        result: List[str] = []

        for item in items:
            item = str(item).strip()

            if not item:
                continue

            if item not in result:
                result.append(item)

        return result

    # --------------------------------------------------------
    # Goal extraction
    # --------------------------------------------------------

    def _extract_goal(
        self,
        message: str,
        decision: Any = None,
        goal: Any = None,
    ) -> str:

        goal_text = self._clean(
            self._value(goal, "text", "")
        )

        if goal_text:
            return goal_text

        decision_goal = self._clean(
            self._value(decision, "goal", "")
        )

        if decision_goal:
            return decision_goal

        return message.strip()

    # --------------------------------------------------------
    # Facts
    # --------------------------------------------------------

    def _extract_facts(
        self,
        message: str,
        decision: Any = None,
        goal: Any = None,
    ) -> List[str]:

        facts: List[str] = []

        intent = self._clean(
            self._value(decision, "intent", "")
        )

        action = self._clean(
            self._value(decision, "action", "")
        )

        target = self._clean(
            self._value(decision, "target", "")
        )

        topic = self._clean(
            self._value(decision, "topic", "")
        )

        query = self._clean(
            self._value(decision, "query", "")
        )

        if intent:
            facts.append(f"intent={intent}")

        if action:
            facts.append(f"action={action}")

        if target:
            facts.append(f"target={target}")

        if topic:
            facts.append(f"topic={topic}")

        if query:
            facts.append(f"query={query}")

        goal_status = self._clean(
            self._value(goal, "status", "")
        )

        if goal_status:
            facts.append(f"goal_status={goal_status}")

        return self._unique(facts)

    # --------------------------------------------------------
    # Missing information
    # --------------------------------------------------------

    def _find_missing(
        self,
        message: str,
        intent: str,
        action: str,
        target: str,
        topic: str,
        decision: Any = None,
    ) -> List[str]:

        missing: List[str] = []

        needs_clarification = bool(
            self._value(
                decision,
                "needs_clarification",
                False,
            )
        )

        if needs_clarification:
            declared_missing = self._value(
                decision,
                "missing",
                [],
            )

            if isinstance(declared_missing, (list, tuple)):
                missing.extend(
                    str(item)
                    for item in declared_missing
                    if str(item).strip()
                )
            elif declared_missing:
                missing.append(str(declared_missing))

        # Action requiring a target.
        if intent == "action":
            if action and not target:
                missing.append("target")

        # Web search normally needs a query/topic.
        if intent == "web":
            query = self._clean(
                self._value(decision, "query", "")
            )

            if not query and not topic:
                missing.append("query")

        return self._unique(missing)

    # --------------------------------------------------------
    # Risk analysis
    # --------------------------------------------------------

    def _find_risks(
        self,
        message: str,
        intent: str,
        action: str,
        target: str,
    ) -> List[str]:

        risks: List[str] = []

        text = message.lower().strip()

        # External computer action.
        if intent == "action":
            risks.append(
                "external_action"
            )

        # Web information can become stale.
        if intent == "web":
            risks.append(
                "information_freshness"
            )

        # Empty / ambiguous input.
        if not text:
            risks.append(
                "empty_input"
            )

        # Commands involving deletion/shutdown are higher impact.
        high_impact_words = (
            "xóa",
            "xoá",
            "delete",
            "shutdown",
            "tắt máy",
            "format",
            "gỡ",
            "uninstall",
        )

        if any(word in text for word in high_impact_words):
            risks.append(
                "high_impact_action"
            )

        return self._unique(risks)

    # --------------------------------------------------------
    # Complexity
    # --------------------------------------------------------

    def _complexity(
        self,
        message: str,
        intent: str,
        risks: List[str],
        missing: List[str],
    ) -> str:

        if missing:
            return "medium"

        if "high_impact_action" in risks:
            return "high"

        words = [
            word
            for word in message.strip().split()
            if word
        ]

        if intent in {
            "follow_up",
            "unknown",
        }:
            return "medium"

        if len(words) >= 20:
            return "medium"

        if intent in {
            "action",
            "time",
            "date",
            "memory",
        }:
            return "low"

        if intent == "web":
            return "medium"

        return "low"

    # --------------------------------------------------------
    # Tool recommendation
    # --------------------------------------------------------

    def _recommend_tool(
        self,
        intent: str,
        action: str,
        target: str,
    ) -> str:

        if intent == "web":
            return "web"

        if intent == "memory":
            return "memory"

        if intent == "action":
            return "action"

        if intent == "time":
            return "system_time"

        if intent == "date":
            return "system_date"

        if intent == "follow_up":
            return "dialogue"

        return "chat"

    # --------------------------------------------------------
    # Plan generation
    # --------------------------------------------------------

    def _build_plan(
        self,
        intent: str,
        action: str,
        target: str,
        missing: List[str],
        recommended_tool: str,
    ) -> List[str]:

        if missing:
            return [
                "clarify_missing_information",
            ]

        if intent == "action":
            return [
                "validate_action",
                "execute_action",
                "verify_result",
            ]

        if intent == "web":
            return [
                "search_information",
                "evaluate_results",
                "prepare_answer",
                "verify_result",
            ]

        if intent == "memory":
            return [
                "process_memory_request",
                "verify_memory_result",
            ]

        if intent in {"time", "date"}:
            return [
                "read_system_information",
                "prepare_answer",
            ]

        if intent == "follow_up":
            return [
                "resolve_context",
                "continue_conversation",
            ]

        if recommended_tool == "chat":
            return [
                "understand_request",
                "generate_answer",
                "verify_answer",
            ]

        return [
            "understand_request",
            "execute_plan",
            "verify_result",
        ]

    # --------------------------------------------------------
    # Main THINK operation
    # --------------------------------------------------------

    def think(
        self,
        message: str,
        decision: Any = None,
        goal: Any = None,
    ) -> ThinkXResult:

        message = self._clean(message)

        intent = self._clean(
            self._value(decision, "intent", "unknown")
        )

        action = self._clean(
            self._value(decision, "action", "")
        )

        target = self._clean(
            self._value(decision, "target", "")
        )

        topic = self._clean(
            self._value(decision, "topic", "")
        )

        query = self._clean(
            self._value(decision, "query", "")
        )

        goal_text = self._extract_goal(
            message,
            decision,
            goal,
        )

        facts = self._extract_facts(
            message,
            decision,
            goal,
        )

        missing = self._find_missing(
            message,
            intent,
            action,
            target,
            topic,
            decision,
        )

        risks = self._find_risks(
            message,
            intent,
            action,
            target,
        )

        complexity = self._complexity(
            message,
            intent,
            risks,
            missing,
        )

        recommended_tool = self._recommend_tool(
            intent,
            action,
            target,
        )

        plan = self._build_plan(
            intent,
            action,
            target,
            missing,
            recommended_tool,
        )

        requires_clarification = bool(missing)

        if requires_clarification:
            reason = (
                "THINK X phát hiện dữ kiện cần làm rõ "
                "trước khi thực hiện."
            )
        elif risks:
            reason = (
                "Mục tiêu đã đủ dữ kiện; "
                "THINK X ghi nhận rủi ro trước khi xử lý."
            )
        else:
            reason = (
                "Mục tiêu đã đủ dữ kiện cơ bản để lập kế hoạch."
            )

        return ThinkXResult(
            message=message,
            goal=goal_text,
            intent=intent,
            action=action,
            target=target,
            topic=topic,
            query=query,
            facts=facts,
            missing=missing,
            risks=risks,
            complexity=complexity,
            requires_clarification=requires_clarification,
            recommended_tool=recommended_tool,
            plan=plan,
            reason=reason,
            metadata={
                "version": self.version,
            },
        )


# ============================================================
# FACTORY
# ============================================================

def create_think_x() -> ThinkXCore:
    return ThinkXCore()


__all__ = [
    "VERSION",
    "ThinkXResult",
    "ThinkXCore",
    "create_think_x",
]
