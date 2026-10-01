"""
MINH MINI - Simulator Core
Version: P10-2.0

Purpose:
    Read-only pre-execution simulation.

This module does NOT:
    - execute actions
    - call Web
    - call Ollama
    - call Action
    - route requests
    - mutate World Model
    - mutate State Manager
    - control execution
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class Simulator:
    VERSION = "P10-2.0"

    VALID_OUTCOMES = {
        "safe",
        "uncertain",
        "blocked",
        "failure",
    }

    VALID_VERDICTS = {
        "pass",
        "review",
        "block",
    }

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
    # GOAL SIMULATION
    # =========================================================

    def _simulate_goal(
        self,
        goal: Any,
        issues: List[str],
        warnings: List[str],
        checks: Dict[str, bool],
    ) -> Dict[str, Any]:
        goal_data = self._as_dict(goal)

        if not goal_data:
            warnings.append("missing_goal")
            checks["goal_present"] = False
            return {}

        checks["goal_present"] = True

        action = self._text(
            goal_data.get("action")
        )

        target = self._text(
            goal_data.get("target")
        )

        text = self._text(
            goal_data.get("text")
        )

        checks["goal_text_present"] = bool(text)
        checks["action_present"] = bool(action)
        checks["target_present"] = bool(target)

        if not text:
            warnings.append("empty_goal")

        if action and not target:
            issues.append("action_missing_target")

        return goal_data

    # =========================================================
    # PLAN SIMULATION
    # =========================================================

    def _simulate_plan(
        self,
        plan: Any,
        issues: List[str],
        warnings: List[str],
        checks: Dict[str, bool],
    ) -> Dict[str, Any]:
        if plan is None:
            checks["plan_present"] = False
            return {}

        plan_data = self._as_dict(plan)

        if not plan_data:
            warnings.append("empty_plan")
            checks["plan_present"] = False
            return {}

        checks["plan_present"] = True

        tasks = plan_data.get("tasks")

        if tasks is None:
            warnings.append("tasks_missing")
            checks["tasks_present"] = False
            return plan_data

        if not isinstance(tasks, list):
            issues.append("tasks_not_list")
            checks["tasks_present"] = False
            return plan_data

        checks["tasks_present"] = True
        checks["tasks_nonempty"] = bool(tasks)

        if not tasks:
            warnings.append("empty_task_plan")
            return plan_data

        active_count = 0
        task_ids: List[str] = []

        for index, task in enumerate(tasks):
            if not isinstance(task, dict):
                issues.append(
                    f"invalid_task_{index}"
                )
                continue

            task_id = self._text(
                task.get("id")
            )

            if task_id:
                task_ids.append(task_id)

            status = self._text(
                task.get("status")
            ).lower()

            if status == "active":
                active_count += 1

        if len(task_ids) != len(set(task_ids)):
            issues.append("duplicate_task_ids")

        if active_count > 1:
            issues.append("multiple_active_tasks")

        return plan_data

    # =========================================================
    # RESULT SIMULATION
    # =========================================================

    def _simulate_result(
        self,
        result: Any,
        issues: List[str],
        warnings: List[str],
        checks: Dict[str, bool],
    ) -> Dict[str, Any]:
        if result is None:
            warnings.append("no_runtime_result")
            checks["result_present"] = False
            return {}

        result_data = self._as_dict(result)

        if not result_data:
            warnings.append("empty_runtime_result")
            checks["result_present"] = False
            return {}

        checks["result_present"] = True

        success = result_data.get("success")

        if success is not None:
            if not isinstance(success, bool):
                issues.append(
                    "invalid_success_type"
                )
                checks[
                    "success_type_valid"
                ] = False
            else:
                checks[
                    "success_type_valid"
                ] = True

        verification = result_data.get(
            "verification"
        )

        if verification is not None:
            if not isinstance(
                verification,
                dict,
            ):
                issues.append(
                    "invalid_verification"
                )
                checks[
                    "verification_valid"
                ] = False
            else:
                checks[
                    "verification_valid"
                ] = True

        return result_data

    # =========================================================
    # OUTCOME PREDICTION
    # =========================================================

    def _predict_outcome(
        self,
        goal_data: Dict[str, Any],
        plan_data: Dict[str, Any],
        result_data: Dict[str, Any],
        issues: List[str],
        warnings: List[str],
    ) -> str:
        if issues:
            return "blocked"

        if not goal_data:
            return "uncertain"

        action = self._text(
            goal_data.get("action")
        )

        target = self._text(
            goal_data.get("target")
        )

        if action and not target:
            return "blocked"

        if result_data:
            success = result_data.get("success")

            if success is False:
                return "failure"

            verification = result_data.get(
                "verification"
            )

            if isinstance(
                verification,
                dict,
            ):
                if (
                    verification.get("verified")
                    is True
                    and verification.get("success")
                    is True
                ):
                    return "safe"

        if warnings:
            return "uncertain"

        return "safe"

    # =========================================================
    # VERDICT
    # =========================================================

    @staticmethod
    def _verdict(
        outcome: str,
        issues: List[str],
        warnings: List[str],
    ) -> str:
        blocking = {
            "action_missing_target",
            "tasks_not_list",
            "duplicate_task_ids",
            "multiple_active_tasks",
            "invalid_success_type",
            "invalid_verification",
        }

        if any(
            item in blocking
            for item in issues
        ):
            return "block"

        if outcome == "blocked":
            return "block"

        if outcome == "failure":
            return "review"

        if issues or warnings:
            return "review"

        return "pass"

    # =========================================================
    # RECOMMENDED ACTION
    # =========================================================

    @staticmethod
    def _recommendation(
        outcome: str,
        verdict: str,
    ) -> str:
        if verdict == "block":
            return "Do not execute; resolve blocking conditions."

        if outcome == "uncertain":
            return "Review simulation before execution."

        if outcome == "failure":
            return "Inspect failure conditions before retrying."

        if verdict == "review":
            return "Review simulation warnings before execution."

        return "Execution may proceed to the next evaluation layer."

    # =========================================================
    # SCORE
    # =========================================================

    @staticmethod
    def _score(
        outcome: str,
        verdict: str,
        issues: List[str],
        warnings: List[str],
    ) -> float:
        score = 1.0

        score -= min(
            0.20 * len(issues),
            0.80,
        )

        score -= min(
            0.05 * len(warnings),
            0.30,
        )

        if outcome == "uncertain":
            score = min(score, 0.65)

        elif outcome == "failure":
            score = min(score, 0.45)

        elif outcome == "blocked":
            score = min(score, 0.20)

        if verdict == "block":
            score = min(score, 0.20)

        elif verdict == "review":
            score = min(score, 0.85)

        return round(
            max(0.0, score),
            2,
        )

    # =========================================================
    # PUBLIC API
    # =========================================================

    def simulate(
        self,
        goal: Any = None,
        plan: Any = None,
        result: Any = None,
    ) -> Dict[str, Any]:
        issues: List[str] = []
        warnings: List[str] = []
        checks: Dict[str, bool] = {}

        goal_data = self._simulate_goal(
            goal,
            issues,
            warnings,
            checks,
        )

        plan_data = self._simulate_plan(
            plan,
            issues,
            warnings,
            checks,
        )

        result_data = self._simulate_result(
            result,
            issues,
            warnings,
            checks,
        )

        outcome = self._predict_outcome(
            goal_data,
            plan_data,
            result_data,
            issues,
            warnings,
        )

        verdict = self._verdict(
            outcome,
            issues,
            warnings,
        )

        score = self._score(
            outcome,
            verdict,
            issues,
            warnings,
        )

        recommendation = self._recommendation(
            outcome,
            verdict,
        )

        if verdict == "pass":
            reason = "Simulation found no material blocking condition."

        elif verdict == "review":
            reason = "Simulation found conditions requiring review."

        else:
            reason = "Simulation found a blocking condition."

        result_data_final = {
            "verdict": verdict,
            "valid": True,
            "outcome": outcome,
            "score": score,
            "issues": list(issues),
            "warnings": list(warnings),
            "checks": dict(checks),
            "recommendation": recommendation,
            "goal": goal,
            "plan": plan,
            "result": result,
            "reason": reason,
            "version": self.VERSION,
        }

        self.last_result = result_data_final

        return result_data_final

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
            == "P10-2.0",
            "outcomes": self.VALID_OUTCOMES
            == {
                "safe",
                "uncertain",
                "blocked",
                "failure",
            },
            "verdicts": self.VALID_VERDICTS
            == {
                "pass",
                "review",
                "block",
            },
            "simulate_callable": callable(
                self.simulate
            ),
            "reset_callable": callable(
                self.reset
            ),
        }

        return {
            "valid": all(checks.values()),
            "checks": checks,
            "version": self.VERSION,
        }

    def status(self) -> Dict[str, Any]:
        return {
            "available": True,
            "version": self.VERSION,
            "has_result": self.last_result is not None,
            "last_result": self.last_result,
        }


def create_simulator() -> Simulator:
    return Simulator()


def self_check() -> Dict[str, Any]:
    simulator = Simulator()

    goal = {
        "text": "mở youtube",
        "action": "open",
        "target": "youtube",
    }

    plan = {
        "tasks": [],
    }

    result = {
        "message": "Đã mở YouTube.",
        "success": True,
        "target": "youtube",
        "verification": {
            "verified": True,
            "status": "pass",
            "success": True,
        },
    }

    evaluated = simulator.simulate(
        goal=goal,
        plan=plan,
        result=result,
    )

    checks = {
        "validate":
            simulator.validate().get("valid")
            is True,

        "result_valid":
            evaluated.get("valid")
            is True,

        "verdict_valid":
            evaluated.get("verdict")
            in Simulator.VALID_VERDICTS,

        "outcome_valid":
            evaluated.get("outcome")
            in Simulator.VALID_OUTCOMES,

        "score_valid":
            isinstance(
                evaluated.get("score"),
                float,
            ),

        "recommendation":
            bool(
                evaluated.get(
                    "recommendation"
                )
            ),
    }

    return {
        "valid": all(checks.values()),
        "checks": checks,
        "result": evaluated,
        "version": Simulator.VERSION,
    }
