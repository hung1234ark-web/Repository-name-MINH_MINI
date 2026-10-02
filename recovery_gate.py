"""MINH MINI P13.2 — Recovery Gate.

Consumes the read-only P13-1 diagnosis/recovery/replan result and turns it into
an explicit next-step gate. This layer never executes, retries, routes,
calls Web/Ollama/Action, or mutates the task planner.

The gate is fail-closed: only a structurally valid P13 success may proceed.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

VERSION = "P13-2.1"
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

    @staticmethod
    def _list(value: Any) -> list[Any]:
        if isinstance(value, list):
            return value
        return [value] if value else []

    def evaluate(self, p13_result: Any = None) -> dict[str, Any]:
        checks: list[str] = []

        if isinstance(p13_result, dict):
            status = self._text(p13_result.get("status"))
            recovery = self._text(p13_result.get("recovery"))
            diagnosis = self._text(p13_result.get("diagnosis"))
            replan = self._list(p13_result.get("replan", []))
        else:
            status = self._text(getattr(p13_result, "status", ""))
            recovery = self._text(getattr(p13_result, "recovery", ""))
            diagnosis = self._text(getattr(p13_result, "diagnosis", ""))
            replan = self._list(getattr(p13_result, "replan", []))

        if not p13_result:
            checks.append("p13_result_missing")
            return RecoveryGateResult(
                "stop", "await_new_instruction", False,
                "No P13 recovery result is available.", checks,
            ).to_dict()
        checks.append("p13_result_present")

        if status == "pass":
            checks.append("p13_pass")
            if recovery != "stop":
                checks.append("success_recovery_invalid")
                return RecoveryGateResult(
                    "stop", "await_new_instruction", False,
                    "P13 pass result has an invalid recovery state.", checks,
                ).to_dict()
            if replan:
                checks.append("success_replan_not_empty")
                return RecoveryGateResult(
                    "stop", "await_new_instruction", False,
                    "P13 pass result contains an unexpected replan.", checks,
                ).to_dict()
            checks.append("success_contract_valid")
            return RecoveryGateResult(
                "proceed", "continue_normal_flow", True,
                "P13 detected no execution or verification failure.", checks,
            ).to_dict()

        if recovery == "clarify":
            checks.append("clarification_required")
            return RecoveryGateResult(
                "clarify", "request_missing_information", False,
                diagnosis or "clarification_required", checks,
            ).to_dict()

        if recovery == "reselect_tool":
            checks.append("tool_reselection_required")
            return RecoveryGateResult(
                "reselect_tool", "reselect_tool_and_rebuild_contract", False,
                diagnosis or "tool_reselection_required", checks,
            ).to_dict()

        if recovery == "replan":
            checks.append("replan_required")
            return RecoveryGateResult(
                "replan", "apply_replan_after_new_authorization", False,
                diagnosis or "replan_required", checks,
            ).to_dict()

        checks.append("recovery_requires_stop")
        return RecoveryGateResult(
            "stop", "await_new_instruction", False,
            diagnosis or "recovery_not_authorized", checks,
        ).to_dict()
    def validate(self) -> dict[str, Any]:
        sample = self.evaluate({
            "status": "review",
            "diagnosis": "verification_failed",
            "recovery": "replan",
            "replan": ["adjust_plan"],
        })
        success = self.evaluate({
            "status": "pass",
            "diagnosis": "no_failure_detected",
            "recovery": "stop",
            "replan": [],
        })
        invalid_success = self.evaluate({
            "status": "pass",
            "diagnosis": "no_failure_detected",
            "recovery": "unexpected",
            "replan": [],
        })
        invalid_success_clarify = self.evaluate({
            "status": "pass",
            "diagnosis": "no_failure_detected",
            "recovery": "clarify",
            "replan": [],
        })
        invalid_success_replan = self.evaluate({
            "status": "pass",
            "diagnosis": "no_failure_detected",
            "recovery": "replan",
            "replan": ["unexpected"],
        })
        checks = {
            "version": self.VERSION == VERSION,
            "result_shape": all(
                key in sample
                for key in (
                    "decision", "action_required",
                    "allowed_to_execute", "reason", "checks",
                )
            ),
            "decision_valid": sample["decision"] in VALID_DECISIONS,
            "execution_forbidden_on_replan": (
                sample["allowed_to_execute"] is False
            ),
            "auto_execution_forbidden": AUTO_EXECUTION_FORBIDDEN,
            "valid_success_proceeds": (
                success["decision"] == "proceed"
                and success["allowed_to_execute"] is True
            ),
            "invalid_success_stops": (
                invalid_success["decision"] == "stop"
                and invalid_success["allowed_to_execute"] is False
            ),
            "pass_clarify_stops": (
                invalid_success_clarify["decision"] == "stop"
                and invalid_success_clarify["allowed_to_execute"] is False
            ),
            "pass_replan_stops": (
                invalid_success_replan["decision"] == "stop"
                and invalid_success_replan["allowed_to_execute"] is False
            ),
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
