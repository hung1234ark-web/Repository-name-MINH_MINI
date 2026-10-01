"""
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
