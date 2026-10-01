"""MINH MINI P13.2 — Recovery Gate.

Consumes the read-only P13-1 diagnosis/recovery/replan result and turns it into
an explicit next-step gate. This layer never executes, retries, routes, calls
Web/Ollama/Action, or mutates the task planner.

The gate exists to make recovery intent observable and to prevent accidental
automatic re-execution.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

VERSION = "P13-2.0"
VALID_DECISIONS = {"proceed", "clarify", "replan", "reselect_tool", "stop"}
AUTO_EXECUTION_FORBIDDEN = True


@dataclass(frozen=True)
class RecoveryGateResult:
    decision: str
    action_required: str
    allowed_to_execute: bool
    reason: str
    checks: list[str]
    version: str = VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RecoveryGate:
    VERSION = VERSION

    @staticmethod
    def _text(value: Any) -> str:
        return str(value or "").strip().lower()

    def evaluate(self, p13_result: Any = None) -> dict[str, Any]:
        checks: list[str] = []

        if isinstance(p13_result, dict):
            status = self._text(p13_result.get("status"))
            recovery = self._text(p13_result.get("recovery"))
            diagnosis = self._text(p13_result.get("diagnosis"))
            replan = p13_result.get("replan", [])
        else:
            status = self._text(getattr(p13_result, "status", ""))
            recovery = self._text(getattr(p13_result, "recovery", ""))
            diagnosis = self._text(getattr(p13_result, "diagnosis", ""))
            replan = getattr(p13_result, "replan", [])

        if not isinstance(replan, list):
            replan = [str(replan)] if replan else []

        if not p13_result:
            checks.append("p13_result_missing")
            return RecoveryGateResult(
                "stop",
                "await_new_instruction",
                False,
                "No P13 recovery result is available.",
                checks,
            ).to_dict()

        checks.append("p13_result_present")

        if recovery == "clarify":
            checks.append("clarification_required")
            return RecoveryGateResult(
                "clarify",
                "request_missing_information",
                False,
                diagnosis or "clarification_required",
                checks,
            ).to_dict()

        if recovery == "reselect_tool":
            checks.append("tool_reselection_required")
            return RecoveryGateResult(
                "reselect_tool",
                "reselect_tool_and_rebuild_contract",
                False,
                diagnosis or "tool_reselection_required",
                checks,
            ).to_dict()

        if recovery == "replan":
            checks.append("replan_required")
            return RecoveryGateResult(
                "replan",
                "apply_replan_after_new_authorization",
                False,
                diagnosis or "replan_required",
                checks,
            ).to_dict()

        if status == "pass":
            checks.append("p13_pass")
            return RecoveryGateResult(
                "proceed",
                "continue_normal_flow",
                True,
                "P13 detected no execution or verification failure.",
                checks,
            ).to_dict()

        checks.append("recovery_requires_stop")
        return RecoveryGateResult(
            "stop",
            "await_new_instruction",
            False,
            diagnosis or "recovery_not_authorized",
            checks,
        ).to_dict()

    def validate(self) -> dict[str, Any]:
        sample = self.evaluate({
            "status": "review",
            "diagnosis": "verification_failed",
            "recovery": "replan",
            "replan": ["adjust_plan"],
        })
        checks = {
            "version": self.VERSION == VERSION,
            "result_shape": all(
                key in sample
                for key in (
                    "decision",
                    "action_required",
                    "allowed_to_execute",
                    "reason",
                    "checks",
                )
            ),
            "decision_valid": sample["decision"] in VALID_DECISIONS,
            "execution_forbidden_on_replan": (
                sample["allowed_to_execute"] is False
            ),
            "auto_execution_forbidden": AUTO_EXECUTION_FORBIDDEN,
        }
        return {
            "valid": all(checks.values()),
            "checks": checks,
            "version": self.VERSION,
        }


def create_recovery_gate() -> RecoveryGate:
    return RecoveryGate()


def self_check() -> dict[str, Any]:
    return create_recovery_gate().validate()
