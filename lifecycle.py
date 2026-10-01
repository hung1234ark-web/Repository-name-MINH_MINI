# ============================================================
# MINH MINI — EXECUTION LIFECYCLE
# P12-3 Runtime Lifecycle
#
# Tracks:
# P12-2 PREPARE
# EXECUTE
# OBSERVE
# VERIFY
#
# This module records lifecycle state only.
# It NEVER executes tools.
# It NEVER calls Web.
# It NEVER calls Ollama.
# It NEVER calls Action.
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


VERSION = "P12-3.0"


@dataclass(frozen=True)
class LifecycleRecord:
    status: str
    stages: list[str]
    completed_stages: list[str]
    failed_stage: str
    verified: bool | None
    success: bool | None
    tool: str
    intent: str
    checks: list[str]
    version: str = VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExecutionLifecycle:
    VERSION = VERSION

    EXPECTED_ORDER = (
        "prepare",
        "execute",
        "observe",
        "verify",
    )

    def __init__(self):
        self.last_lifecycle: LifecycleRecord | None = None
        self._stages: list[str] = []

    def reset(self) -> None:
        self._stages = []

    def record(self, stage: str) -> dict[str, Any]:
        stage = str(stage or "").strip().lower()

        if stage not in self.EXPECTED_ORDER:
            raise ValueError(
                f"invalid_lifecycle_stage:{stage}"
            )

        expected_index = len(self._stages)

        if expected_index >= len(self.EXPECTED_ORDER):
            raise ValueError(
                "lifecycle_already_complete"
            )

        expected_stage = self.EXPECTED_ORDER[
            expected_index
        ]

        if stage != expected_stage:
            raise ValueError(
                "lifecycle_order_violation:"
                + expected_stage
                + "->"
                + stage
            )

        self._stages.append(stage)

        return {
            "stage": stage,
            "stages": list(self._stages),
            "version": self.VERSION,
        }

    def finalize(
        self,
        *,
        verified: bool | None = None,
        success: bool | None = None,
        tool: str = "",
        intent: str = "",
        error: str = "",
    ) -> dict[str, Any]:

        stages = list(self._stages)
        checks: list[str] = []

        if stages == list(self.EXPECTED_ORDER):
            checks.append("lifecycle_order_pass")
        else:
            checks.append("lifecycle_order_incomplete")

        if verified is True:
            checks.append("verification_pass")
        elif verified is False:
            checks.append("verification_fail")
        else:
            checks.append("verification_unknown")

        if success is True:
            checks.append("execution_success")
        elif success is False:
            checks.append("execution_failure")
        else:
            checks.append("execution_unknown")

        if error:
            checks.append("error_present")

        if (
            stages == list(self.EXPECTED_ORDER)
            and verified is True
            and success is True
        ):
            status = "pass"
        elif verified is False or success is False:
            status = "fail"
        else:
            status = "review"

        failed_stage = ""

        if status == "fail":
            if "verify" in stages and verified is False:
                failed_stage = "verify"
            elif "execute" in stages and success is False:
                failed_stage = "execute"
            elif "observe" not in stages:
                failed_stage = "observe"
            elif "execute" not in stages:
                failed_stage = "execute"
            elif "prepare" not in stages:
                failed_stage = "prepare"

        record = LifecycleRecord(
            status=status,
            stages=stages,
            completed_stages=stages,
            failed_stage=failed_stage,
            verified=verified
            if isinstance(verified, bool)
            else None,
            success=success
            if isinstance(success, bool)
            else None,
            tool=str(tool or "").strip(),
            intent=str(intent or "").strip(),
            checks=checks,
        )

        self.last_lifecycle = record
        return record.to_dict()


def create_execution_lifecycle() -> ExecutionLifecycle:
    return ExecutionLifecycle()


__all__ = [
    "VERSION",
    "LifecycleRecord",
    "ExecutionLifecycle",
    "create_execution_lifecycle",
]
