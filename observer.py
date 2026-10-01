# ============================================================
# MINH MINI — OBSERVER
# P12-1 Execute -> Observe -> Verify
#
# Observer chỉ ghi nhận execution result đã có.
# Không execute.
# Không retry.
# Không gọi Web.
# Không gọi Ollama.
# Không gọi Action.
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


VERSION = "P12-1.0"


@dataclass(frozen=True)
class Observation:
    observed: bool
    success: bool | None
    tool: str
    intent: str
    answer: str
    error: str
    raw_type: str
    checks: list[str]
    version: str = VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Observer:
    VERSION = VERSION

    def __init__(self):
        self.last_observation: Observation | None = None

    @staticmethod
    def _value(
        value: Any,
        key: str,
        default: Any = None,
    ) -> Any:
        if value is None:
            return default

        if isinstance(value, dict):
            return value.get(key, default)

        return getattr(
            value,
            key,
            default,
        )

    @staticmethod
    def _text(value: Any) -> str:
        if value is None:
            return ""

        return str(value).strip()

    def observe(
        self,
        *,
        message: str = "",
        decision: Any = None,
        execution_result: Any = None,
        answer: str = "",
    ) -> dict[str, Any]:

        checks: list[str] = []

        if execution_result is None:
            observation = Observation(
                observed=False,
                success=None,
                tool="",
                intent=self._text(
                    self._value(
                        decision,
                        "intent",
                        "",
                    )
                ),
                answer=self._text(answer),
                error="missing_execution_result",
                raw_type="NoneType",
                checks=[
                    "missing_execution_result",
                ],
            )

            self.last_observation = observation
            return observation.to_dict()

        success = self._value(
            execution_result,
            "success",
            None,
        )

        tool = self._text(
            self._value(
                execution_result,
                "tool",
                "",
            )
        )

        intent = self._text(
            self._value(
                execution_result,
                "intent",
                self._value(
                    decision,
                    "intent",
                    "",
                ),
            )
        )

        error = self._text(
            self._value(
                execution_result,
                "error",
                "",
            )
        )

        answer_text = self._text(answer)

        checks.append("execution_result_present")

        if success is True:
            checks.append("success_true")
        elif success is False:
            checks.append("success_false")
        else:
            checks.append("success_unknown")

        if tool:
            checks.append("tool_present")
        else:
            checks.append("tool_missing")

        if answer_text:
            checks.append("answer_present")
        else:
            checks.append("answer_missing")

        if error:
            checks.append("error_present")

        observation = Observation(
            observed=True,
            success=success
            if isinstance(success, bool)
            else None,
            tool=tool,
            intent=intent,
            answer=answer_text,
            error=error,
            raw_type=type(execution_result).__name__,
            checks=checks,
        )

        self.last_observation = observation

        return observation.to_dict()


def create_observer() -> Observer:
    return Observer()


__all__ = [
    "VERSION",
    "Observation",
    "Observer",
    "create_observer",
]
