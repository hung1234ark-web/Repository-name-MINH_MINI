"""MINH MINI P13.1 — Diagnosis -> Recovery -> Replan.

Read-only recovery planner. It never executes tools, retries actions, calls Web/Ollama,
or mutates existing execution state. It converts a failed execution/verification result
into a deterministic diagnosis, recovery strategy, and replanned next step.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

VERSION = "P13-1.0"
VALID_RECOVERY = {"clarify", "repair_input", "reselect_tool", "replan", "stop"}
VALID_STATUS = {"pass", "fail", "review"}

@dataclass(frozen=True)
class P13Result:
    status: str
    diagnosis: str
    recovery: str
    replan: list[str]
    reason: str
    checks: list[str]
    version: str = VERSION
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

class DiagnosisRecoveryReplan:
    VERSION = VERSION

    @staticmethod
    def _value(obj: Any, key: str, default: Any = None) -> Any:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default) if obj is not None else default

    @staticmethod
    def _text(value: Any) -> str:
        return str(value or "").strip()

    def analyze(self, *, message: str = "", decision: Any = None,
                execution_result: Any = None, verification: Any = None,
                lifecycle: Any = None) -> dict[str, Any]:
        checks: list[str] = []
        success = self._value(execution_result, "success", None)
        verified = self._value(verification, "verified", None)
        error = self._text(self._value(execution_result, "error", ""))
        intent = self._text(self._value(decision, "intent", ""))
        tool = self._text(self._value(execution_result, "tool",
                                       self._value(decision, "tool", "")))
        blockers = self._value(decision, "constraints", [])
        if not isinstance(blockers, list):
            blockers = [str(blockers)] if blockers else []

        if success is True and verified is True:
            checks += ["execution_success", "verification_pass"]
            return P13Result("pass", "no_failure_detected", "stop", [],
                              "Execution and verification both passed.", checks).to_dict()

        checks.append("failure_or_uncertainty_detected")
        if verified is False:
            diagnosis = "verification_failed"
        elif success is False:
            diagnosis = "execution_failed"
        elif execution_result is None:
            diagnosis = "missing_execution_result"
        elif error:
            diagnosis = "execution_error_present"
        else:
            diagnosis = "execution_outcome_uncertain"

        if "missing_information" in blockers or not message.strip():
            recovery = "clarify"
            plan = ["request_missing_information", "rebuild_execution_contract"]
        elif not tool and intent in {"action", "web", "memory", "time", "date"}:
            recovery = "reselect_tool"
            plan = ["reselect_tool", "rebuild_execution_contract"]
        elif intent == "action" and diagnosis in {"execution_failed", "execution_error_present"}:
            recovery = "replan"
            plan = ["inspect_failed_action", "adjust_action_plan", "await_reexecution_authorization"]
        elif diagnosis == "verification_failed":
            recovery = "replan"
            plan = ["inspect_verification_failure", "adjust_plan", "await_reexecution_authorization"]
        else:
            recovery = "stop"
            plan = ["record_failure", "await_new_instruction"]

        reason = f"{diagnosis}; recovery={recovery}"
        return P13Result("review" if recovery != "stop" else "fail",
                         diagnosis, recovery, plan, reason, checks).to_dict()

    def validate(self) -> dict[str, Any]:
        sample = self.analyze(
            message="test",
            decision={"intent": "action", "tool": "action"},
            execution_result={"success": False, "tool": "action", "error": "test"},
            verification={"verified": False},
        )
        checks = {
            "version": self.VERSION == "P13-1.0",
            "result_shape": all(k in sample for k in
                                ("status", "diagnosis", "recovery", "replan", "checks")),
            "recovery_valid": sample["recovery"] in VALID_RECOVERY,
            "no_execution_flag": True,
        }
        return {"valid": all(checks.values()), "checks": checks, "version": self.VERSION}

def create_diagnosis_recovery_replan() -> DiagnosisRecoveryReplan:
    return DiagnosisRecoveryReplan()

def self_check() -> dict[str, Any]:
    return create_diagnosis_recovery_replan().validate()
