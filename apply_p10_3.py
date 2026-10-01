from pathlib import Path
import py_compile
import sys

ROOT = Path(__file__).resolve().parent
JUDGE = ROOT / "judge.py"

SOURCE = r'''"""
MINH MINI - Judge Core
Version: P10-3.0

Purpose:
    Aggregate evaluation results and produce a final
    pre-execution decision.

This module does NOT:
    - execute actions
    - call Web
    - call Ollama
    - call Action
    - route requests
    - mutate World Model
    - mutate State Manager
    - modify other evaluation modules
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class Judge:
    VERSION = "P10-3.0"

    VALID_VERDICTS = {
        "pass",
        "review",
        "block",
    }

    VALID_DECISIONS = {
        "proceed",
        "review",
        "stop",
    }

    EVALUATORS = (
        "critic",
        "red_team",
        "fact_check",
        "combined",
        "risk",
        "simulator",
    )

    def __init__(self) -> None:
        self.last_result: Optional[Dict[str, Any]] = None

    # =========================================================
    # NORMALIZATION
    # =========================================================

    @staticmethod
    def _as_dict(value: Any) -> Dict[str, Any]:
        if isinstance(value, dict):
            return value

        if value is None:
            return {}

        data = getattr(value, "__dict__", None)

        if isinstance(data, dict):
            return dict(data)

        return {}

    @staticmethod
    def _text(value: Any) -> str:
        if value is None:
            return ""

        return str(value).strip()

    # =========================================================
    # VERDICT NORMALIZATION
    # =========================================================

    @classmethod
    def _normalize_verdict(
        cls,
        value: Any,
    ) -> Optional[str]:
        text = cls._text(value).lower()

        if text in cls.VALID_VERDICTS:
            return text

        return None

    # =========================================================
    # EVALUATOR READING
    # =========================================================

    def _read_evaluator(
        self,
        name: str,
        value: Any,
        issues: List[str],
        warnings: List[str],
        checks: Dict[str, bool],
    ) -> Dict[str, Any]:
        data = self._as_dict(value)

        if not data:
            checks[f"{name}_present"] = False
            return {}

        checks[f"{name}_present"] = True

        verdict = self._normalize_verdict(
            data.get("verdict")
        )

        if verdict is None:
            issues.append(
                f"{name}_invalid_verdict"
            )
            checks[
                f"{name}_verdict_valid"
            ] = False
        else:
            checks[
                f"{name}_verdict_valid"
            ] = True

        valid = data.get("valid")

        if valid is not None:
            if not isinstance(valid, bool):
                issues.append(
                    f"{name}_invalid_valid_type"
                )
                checks[
                    f"{name}_valid_type"
                ] = False
            else:
                checks[
                    f"{name}_valid_type"
                ] = True

        return data

    # =========================================================
    # RESULT COLLECTION
    # =========================================================

    def _collect(
        self,
        evaluations: Dict[str, Any],
        issues: List[str],
        warnings: List[str],
        checks: Dict[str, bool],
    ) -> Dict[str, Dict[str, Any]]:
        collected: Dict[str, Dict[str, Any]] = {}

        for name in self.EVALUATORS:
            if name not in evaluations:
                continue

            data = self._read_evaluator(
                name,
                evaluations.get(name),
                issues,
                warnings,
                checks,
            )

            if data:
                collected[name] = data

        if not collected:
            issues.append(
                "no_evaluator_results"
            )
            checks["evaluators_available"] = False
        else:
            checks["evaluators_available"] = True

        return collected

    # =========================================================
    # VERDICT AGGREGATION
    # =========================================================

    @staticmethod
    def _aggregate_verdict(
        collected: Dict[str, Dict[str, Any]],
    ) -> str:
        verdicts = []

        for data in collected.values():
            verdict = Judge._normalize_verdict(
                data.get("verdict")
            )

            if verdict is not None:
                verdicts.append(verdict)

        if not verdicts:
            return "block"

        if "block" in verdicts:
            return "block"

        if "review" in verdicts:
            return "review"

        return "pass"

    # =========================================================
    # DECISION
    # =========================================================

    @staticmethod
    def _decision(
        verdict: str,
        risk: Optional[Dict[str, Any]],
        simulator: Optional[Dict[str, Any]],
    ) -> str:
        if verdict == "block":
            return "stop"

        if risk:
            risk_verdict = Judge._normalize_verdict(
                risk.get("verdict")
            )

            risk_level = Judge._text(
                risk.get("risk_level")
            ).lower()

            if risk_verdict == "block":
                return "stop"

            if risk_level in {
                "critical",
                "high",
            }:
                return "stop"

        if simulator:
            simulator_verdict = Judge._normalize_verdict(
                simulator.get("verdict")
            )

            outcome = Judge._text(
                simulator.get("outcome")
            ).lower()

            if simulator_verdict == "block":
                return "stop"

            if outcome in {
                "blocked",
            }:
                return "stop"

            if outcome in {
                "uncertain",
                "failure",
            }:
                return "review"

        if verdict == "review":
            return "review"

        return "proceed"

    # =========================================================
    # SCORE
    # =========================================================

    @staticmethod
    def _score(
        verdict: str,
        decision: str,
        collected: Dict[str, Dict[str, Any]],
    ) -> float:
        scores: List[float] = []

        for data in collected.values():
            value = data.get("score")

            if isinstance(value, bool):
                continue

            if isinstance(value, (int, float)):
                scores.append(
                    max(
                        0.0,
                        min(
                            1.0,
                            float(value),
                        ),
                    )
                )

        if scores:
            score = sum(scores) / len(scores)
        else:
            if decision == "stop":
                score = 0.20
            elif decision == "review":
                score = 0.60
            else:
                score = 0.90

        if verdict == "block":
            score = min(score, 0.20)

        elif verdict == "review":
            score = min(score, 0.85)

        if decision == "stop":
            score = min(score, 0.20)

        elif decision == "review":
            score = min(score, 0.70)

        return round(
            max(0.0, min(1.0, score)),
            2,
        )

    # =========================================================
    # REASON
    # =========================================================

    @staticmethod
    def _reason(
        verdict: str,
        decision: str,
    ) -> str:
        if decision == "stop":
            return (
                "Judge found a condition that "
                "requires stopping before execution."
            )

        if decision == "review":
            return (
                "Judge found conditions that "
                "require review before execution."
            )

        return (
            "Judge found no blocking condition "
            "and permits progression to execution."
        )

    # =========================================================
    # RECOMMENDATION
    # =========================================================

    @staticmethod
    def _recommendation(
        decision: str,
    ) -> str:
        if decision == "stop":
            return (
                "Do not execute. Resolve blocking "
                "conditions first."
            )

        if decision == "review":
            return (
                "Review evaluator results before "
                "allowing execution."
            )

        return (
            "Proceed to the next execution-control layer."
        )

    # =========================================================
    # PUBLIC API
    # =========================================================

    def evaluate(
        self,
        critic: Any = None,
        red_team: Any = None,
        fact_check: Any = None,
        combined: Any = None,
        risk: Any = None,
        simulator: Any = None,
    ) -> Dict[str, Any]:
        evaluations = {
            "critic": critic,
            "red_team": red_team,
            "fact_check": fact_check,
            "combined": combined,
            "risk": risk,
            "simulator": simulator,
        }

        issues: List[str] = []
        warnings: List[str] = []
        checks: Dict[str, bool] = {}

        collected = self._collect(
            evaluations,
            issues,
            warnings,
            checks,
        )

        # Missing optional evaluator modules are warnings.
        for name in self.EVALUATORS:
            if name not in collected:
                if name in evaluations:
                    warnings.append(
                        f"{name}_unavailable"
                    )

        verdict = self._aggregate_verdict(
            collected
        )

        risk_data = collected.get("risk")
        simulator_data = collected.get(
            "simulator"
        )

        decision = self._decision(
            verdict,
            risk_data,
            simulator_data,
        )

        score = self._score(
            verdict,
            decision,
            collected,
        )

        if decision == "stop":
            status = "blocked"
        elif decision == "review":
            status = "review"
        else:
            status = "ready"

        reason = self._reason(
            verdict,
            decision,
        )

        recommendation = self._recommendation(
            decision,
        )

        result = {
            "verdict": verdict,
            "decision": decision,
            "status": status,
            "valid": True,
            "score": score,
            "issues": list(issues),
            "warnings": list(warnings),
            "checks": dict(checks),
            "evaluations": dict(collected),
            "reason": reason,
            "recommendation": recommendation,
            "version": self.VERSION,
        }

        self.last_result = result

        return result

    def get_last_result(
        self,
    ) -> Optional[Dict[str, Any]]:
        if self.last_result is None:
            return None

        return dict(self.last_result)

    def reset(self) -> None:
        self.last_result = None

    def validate(self) -> Dict[str, Any]:
        checks = {
            "version": self.VERSION
            == "P10-3.0",

            "verdicts":
                self.VALID_VERDICTS
                == {
                    "pass",
                    "review",
                    "block",
                },

            "decisions":
                self.VALID_DECISIONS
                == {
                    "proceed",
                    "review",
                    "stop",
                },

            "evaluators":
                self.EVALUATORS
                == (
                    "critic",
                    "red_team",
                    "fact_check",
                    "combined",
                    "risk",
                    "simulator",
                ),

            "evaluate_callable":
                callable(self.evaluate),

            "reset_callable":
                callable(self.reset),
        }

        return {
            "valid": all(
                checks.values()
            ),
            "checks": checks,
            "version": self.VERSION,
        }

    def status(self) -> Dict[str, Any]:
        return {
            "available": True,
            "version": self.VERSION,
            "has_result":
                self.last_result is not None,
            "last_result":
                self.last_result,
        }


def create_judge() -> Judge:
    return Judge()


def self_check() -> Dict[str, Any]:
    judge = Judge()

    critic = {
        "verdict": "pass",
        "valid": True,
        "score": 0.90,
    }

    red_team = {
        "verdict": "pass",
        "valid": True,
        "score": 0.90,
    }

    fact_check = {
        "verdict": "pass",
        "valid": True,
        "score": 1.00,
    }

    combined = {
        "verdict": "pass",
        "valid": True,
        "score": 0.93,
    }

    risk = {
        "verdict": "pass",
        "valid": True,
        "risk_level": "low",
        "score": 0.90,
    }

    simulator = {
        "verdict": "pass",
        "valid": True,
        "outcome": "safe",
        "score": 0.90,
    }

    result = judge.evaluate(
        critic=critic,
        red_team=red_team,
        fact_check=fact_check,
        combined=combined,
        risk=risk,
        simulator=simulator,
    )

    checks = {
        "validate":
            judge.validate().get("valid")
            is True,

        "result_valid":
            result.get("valid")
            is True,

        "verdict_valid":
            result.get("verdict")
            in Judge.VALID_VERDICTS,

        "decision_valid":
            result.get("decision")
            in Judge.VALID_DECISIONS,

        "status_valid":
            result.get("status")
            in {
                "ready",
                "review",
                "blocked",
            },

        "proceed_case":
            result.get("decision")
            == "proceed",
    }

    return {
        "valid": all(
            checks.values()
        ),
        "checks": checks,
        "result": result,
        "version": Judge.VERSION,
    }
'''

print("=== P10-3 JUDGE CORE ===")

JUDGE.write_text(
    SOURCE,
    encoding="utf-8",
)

print("SOURCE WRITE: PASS")

py_compile.compile(
    str(JUDGE),
    doraise=True,
)

print("COMPILE: PASS")

sys.path.insert(
    0,
    str(ROOT),
)

from judge import (
    Judge,
    create_judge,
    self_check,
)

judge = create_judge()

# =========================================================
# CORE VALIDATION
# =========================================================

validation = judge.validate()

if validation.get("valid") is not True:
    raise RuntimeError(
        f"VALIDATION FAILED: {validation}"
    )

print("VALIDATION: PASS")

# =========================================================
# OBJECT NORMALIZATION
# =========================================================

from types import SimpleNamespace

object_result = SimpleNamespace(
    verdict="pass",
    valid=True,
    score=0.90,
)

normalized = Judge._as_dict(
    object_result
)

if normalized.get("verdict") != "pass":
    raise RuntimeError(
        f"OBJECT NORMALIZATION FAILED: {normalized}"
    )

print("OBJECT NORMALIZATION: PASS")

# =========================================================
# PROCEED CASE
# =========================================================

common_pass = {
    "verdict": "pass",
    "valid": True,
    "score": 0.90,
}

risk_pass = {
    "verdict": "pass",
    "valid": True,
    "risk_level": "low",
    "score": 0.90,
}

simulator_pass = {
    "verdict": "pass",
    "valid": True,
    "outcome": "safe",
    "score": 0.90,
}

proceed = judge.evaluate(
    critic=common_pass,
    red_team=common_pass,
    fact_check=common_pass,
    combined=common_pass,
    risk=risk_pass,
    simulator=simulator_pass,
)

print(
    "PROCEED CASE:",
    proceed,
)

if proceed.get("decision") != "proceed":
    raise RuntimeError(
        "PROCEED DECISION FAILED"
    )

if proceed.get("status") != "ready":
    raise RuntimeError(
        "PROCEED STATUS FAILED"
    )

print("PROCEED CASE: PASS")

# =========================================================
# REVIEW CASE
# =========================================================

review = judge.evaluate(
    critic={
        "verdict": "review",
        "valid": True,
        "score": 0.70,
    },
    red_team={
        "verdict": "pass",
        "valid": True,
        "score": 0.90,
    },
    fact_check={
        "verdict": "pass",
        "valid": True,
        "score": 0.90,
    },
    combined={
        "verdict": "review",
        "valid": True,
        "score": 0.75,
    },
    risk={
        "verdict": "review",
        "valid": True,
        "risk_level": "medium",
        "score": 0.65,
    },
    simulator={
        "verdict": "review",
        "valid": True,
        "outcome": "uncertain",
        "score": 0.60,
    },
)

print(
    "REVIEW CASE:",
    review,
)

if review.get("decision") != "review":
    raise RuntimeError(
        "REVIEW DECISION FAILED"
    )

if review.get("status") != "review":
    raise RuntimeError(
        "REVIEW STATUS FAILED"
    )

print("REVIEW CASE: PASS")

# =========================================================
# BLOCK CASE
# =========================================================

block = judge.evaluate(
    critic={
        "verdict": "pass",
        "valid": True,
        "score": 0.90,
    },
    red_team={
        "verdict": "block",
        "valid": True,
        "score": 0.20,
    },
    fact_check={
        "verdict": "pass",
        "valid": True,
        "score": 0.90,
    },
    combined={
        "verdict": "block",
        "valid": True,
        "score": 0.20,
    },
    risk={
        "verdict": "critical",
        "valid": True,
        "risk_level": "critical",
        "score": 0.10,
    },
    simulator={
        "verdict": "block",
        "valid": True,
        "outcome": "blocked",
        "score": 0.10,
    },
)

print(
    "BLOCK CASE:",
    block,
)

if block.get("decision") != "stop":
    raise RuntimeError(
        "BLOCK DECISION FAILED"
    )

if block.get("status") != "blocked":
    raise RuntimeError(
        "BLOCK STATUS FAILED"
    )

print("BLOCK CASE: PASS")

# =========================================================
# NO EVALUATORS
# =========================================================

empty = judge.evaluate()

print(
    "EMPTY CASE:",
    empty,
)

if empty.get("verdict") != "block":
    raise RuntimeError(
        "EMPTY EVALUATION MUST BLOCK"
    )

if empty.get("decision") != "stop":
    raise RuntimeError(
        "EMPTY EVALUATION MUST STOP"
    )

print("EMPTY CASE: PASS")

# =========================================================
# SELF CHECK
# =========================================================

self_check_result = self_check()

if self_check_result.get("valid") is not True:
    raise RuntimeError(
        f"SELF CHECK FAILED: {self_check_result}"
    )

print("SELF CHECK: PASS")

# =========================================================
# RESET
# =========================================================

judge.reset()

if judge.get_last_result() is not None:
    raise RuntimeError(
        "RESET FAILED"
    )

print("RESET: PASS")

# =========================================================
# STATUS
# =========================================================

status = judge.status()

if status.get("available") is not True:
    raise RuntimeError(
        "STATUS FAILED"
    )

print("STATUS: PASS")

# =========================================================
# FINAL
# =========================================================

print()
print("=== FINAL ===")
print("P10-3 JUDGE CORE: PASS")
print("MAIN.PY: NOT MODIFIED")
print("P9: NOT MODIFIED")
print("P10-1 RISK: NOT MODIFIED")
print("P10-2 SIMULATOR: NOT MODIFIED")
print("EXECUTION CONTROL: NO")
print("WEB/OLLAMA: NO")
print("AUTO EXECUTION: NO")
print("AUTO GIT COMMIT: NO")
