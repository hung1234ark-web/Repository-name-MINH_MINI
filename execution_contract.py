"""
MINH MINI
EXECUTION CONTRACT CORE
P4-3.0

Vai trò:
- Nhận quyết định từ Meta-Orchestrator.
- Chuyển quyết định đó thành Execution Contract.
- Xác định có được phép chuyển sang Execution hay không.
- Không trực tiếp thực thi action/web/memory/system.
- Không gọi Ollama.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


VERSION = "P4-3.0"


@dataclass
class ExecutionContract:
    """Hợp đồng giữa bộ não điều phối và tầng thực thi."""

    message: str = ""

    allowed: bool = False

    tool: str = ""
    operation: str = ""
    target: str = ""

    mode: str = "blocked"

    verify_required: bool = True

    blockers: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    steps: List[str] = field(default_factory=list)

    reason: str = ""

    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message": self.message,
            "allowed": self.allowed,
            "tool": self.tool,
            "operation": self.operation,
            "target": self.target,
            "mode": self.mode,
            "verify_required": self.verify_required,
            "blockers": list(self.blockers),
            "requirements": list(self.requirements),
            "steps": list(self.steps),
            "reason": self.reason,
            "metadata": dict(self.metadata),
        }


class ExecutionContractBuilder:
    """
    Tạo Execution Contract từ Meta-Orchestrator.

    Nguyên tắc:
    1. Clarification không được phép execute.
    2. Thiếu dữ kiện không được phép execute.
    3. Tool phải tồn tại với các nhánh có thực thi.
    4. Action phải có operation.
    5. Action cần target khi target được yêu cầu.
    6. Contract luôn yêu cầu verification.
    """

    VERSION = VERSION

    # --------------------------------------------------------
    # SAFE HELPERS
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
        result = []

        for item in items:
            if item and item not in result:
                result.append(item)

        return result

    # --------------------------------------------------------
    # OPERATION
    # --------------------------------------------------------

    def _operation(
        self,
        intent: str,
        action: str,
        next_step: str,
    ) -> str:

        if intent == "action":
            return action or "execute"

        if intent == "web":
            return "search"

        if intent == "memory":
            return "memory"

        if intent == "time":
            return "read_time"

        if intent == "date":
            return "read_date"

        if intent == "follow_up":
            return "continue"

        if next_step == "chat":
            return "respond"

        return ""

    # --------------------------------------------------------
    # TOOL
    # --------------------------------------------------------

    def _tool(
        self,
        meta: Any,
        intent: str,
    ) -> str:

        tool = self._clean(
            self._value(meta, "tool", "")
        )

        if tool:
            return tool

        defaults = {
            "action": "action",
            "web": "web",
            "memory": "memory",
            "time": "system_time",
            "date": "system_date",
        }

        return defaults.get(intent, "")

    # --------------------------------------------------------
    # REQUIREMENTS
    # --------------------------------------------------------

    def _requirements(
        self,
        intent: str,
        operation: str,
        target: str,
    ) -> List[str]:

        requirements = []

        if intent == "action":
            requirements.append("valid_action")

            if operation:
                requirements.append("operation")

            if target:
                requirements.append("target")

        elif intent == "web":
            requirements.append("search_query")

        elif intent == "memory":
            requirements.append("memory_request")

        elif intent == "time":
            requirements.append("system_clock")

        elif intent == "date":
            requirements.append("system_date")

        return requirements

    # --------------------------------------------------------
    # BLOCKERS
    # --------------------------------------------------------

    def _blockers(
        self,
        meta: Any,
        intent: str,
        tool: str,
        operation: str,
        target: str,
    ) -> List[str]:

        blockers = []

        mode = self._clean(
            self._value(meta, "mode", "")
        )

        next_step = self._clean(
            self._value(meta, "next_step", "")
        )

        constraints = self._value(
            meta,
            "constraints",
            [],
        )

        if not isinstance(constraints, list):
            constraints = [str(constraints)] if constraints else []

        if mode == "clarify":
            blockers.append(
                "clarification_required"
            )

        if next_step == "clarify":
            blockers.append(
                "clarification_required"
            )

        if "missing_information" in constraints:
            blockers.append(
                "missing_information"
            )

        if not intent:
            blockers.append(
                "missing_intent"
            )

        if not tool and intent in {
            "action",
            "web",
            "memory",
            "time",
            "date",
        }:
            blockers.append(
                "missing_tool"
            )

        if intent == "action" and not operation:
            blockers.append(
                "missing_operation"
            )

        if (
            intent == "action"
            and not target
        ):
            blockers.append(
                "missing_target"
            )

        return self._unique(blockers)

    # --------------------------------------------------------
    # STEPS
    # --------------------------------------------------------

    def _steps(
        self,
        intent: str,
        operation: str,
        verify_required: bool,
    ) -> List[str]:

        if intent == "action":
            steps = [
                "validate_contract",
                "execute_action",
            ]

        elif intent == "web":
            steps = [
                "validate_contract",
                "search_information",
            ]

        elif intent == "memory":
            steps = [
                "validate_contract",
                "process_memory",
            ]

        elif intent == "time":
            steps = [
                "validate_contract",
                "read_system_time",
            ]

        elif intent == "date":
            steps = [
                "validate_contract",
                "read_system_date",
            ]

        else:
            steps = [
                "validate_contract",
                "respond",
            ]

        if verify_required:
            steps.append("verify_result")

        return steps

    # --------------------------------------------------------
    # BUILD
    # --------------------------------------------------------

    def build(
        self,
        message: str,
        meta: Any = None,
    ) -> ExecutionContract:

        message = self._clean(message)

        intent = self._clean(
            self._value(meta, "intent", "")
        )

        action = self._clean(
            self._value(meta, "action", "")
        )

        target = self._clean(
            self._value(meta, "target", "")
        )

        next_step = self._clean(
            self._value(meta, "next_step", "")
        )

        tool = self._tool(
            meta,
            intent,
        )

        operation = self._operation(
            intent,
            action,
            next_step,
        )

        blockers = self._blockers(
            meta,
            intent,
            tool,
            operation,
            target,
        )

        requirements = self._requirements(
            intent,
            operation,
            target,
        )

        allowed = (
            len(blockers) == 0
            and next_step in {
                "execute",
                "delegate",
            }
        )

        if allowed:
            mode = "ready"
            reason = (
                "Đủ điều kiện để chuyển sang "
                "tầng thực thi."
            )
        elif blockers:
            mode = "blocked"
            reason = (
                "Chưa được phép thực thi vì: "
                + ", ".join(blockers)
            )
        else:
            mode = "not_execution"
            reason = (
                "Meta-Orchestrator chưa yêu cầu "
                "chuyển sang tầng thực thi."
            )

        verify_required = True

        steps = self._steps(
            intent,
            operation,
            verify_required,
        )

        contract = ExecutionContract(
            message=message,
            allowed=allowed,
            tool=tool,
            operation=operation,
            target=target,
            mode=mode,
            verify_required=verify_required,
            blockers=blockers,
            requirements=requirements,
            steps=steps,
            reason=reason,
            metadata={
                "version": self.VERSION,
                "intent": intent,
                "next_step": next_step,
            },
        )

        return contract


def create_execution_contract_builder() -> ExecutionContractBuilder:
    return ExecutionContractBuilder()


__all__ = [
    "VERSION",
    "ExecutionContract",
    "ExecutionContractBuilder",
    "create_execution_contract_builder",
]
