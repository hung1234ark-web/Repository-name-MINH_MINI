"""
MINH MINI - Risk Core
Version: P10-1.0

Purpose:
    Read-only risk evaluation for goals, plans and execution results.

This module does NOT:
    - execute actions
    - route requests
    - call Ollama
    - call Web
    - mutate World Model
    - mutate State Manager
    - control execution
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class Risk:
    VERSION = "P10-1.0"

    VALID_LEVELS = {
        "low",
        "medium",
        "high",
        "critical",
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
    # GOAL RISK
    # =========================================================

    def _check_goal(
        self,
        goal: Any,
        risks: List[str],
        warnings: List[str],
        checks: Dict[str, bool],
    ) -> None:
        if goal is None:
            warnings.append("missing_goal")
            checks["goal_present"] = False
            return

        goal_data = self._as_dict(goal)

        if not goal_data:
            risks.append("unreadable_goal")
            checks["goal_present"] = False
            return

        checks["goal_present"] = True

        text = self._text(goal_data.get("text"))
        action = self._text(goal_data.get("action"))
        target = self._text(goal_data.get("target"))

        checks["goal_text_present"] = bool(text)
        checks["action_present"] = bool(action)
        checks["target_present"] = bool(target)

        if not text:
            warnings.append("empty_goal_text")

        if action and not target:
            warnings.append("action_without_target")

    # =========================================================
    # PLAN RISK
    # =========================================================

    def _check_plan(
        self,
        plan: Any,
        risks: List[str],
        warnings: List[str],
        checks: Dict[str, bool],
    ) -> None:
        if plan is None:
            checks["plan_present"] = False
            return

        plan_data = self._as_dict(plan)

        if not plan_data:
            warnings.append("empty_plan_object")
            checks["plan_present"] = False
            return

        checks["plan_present"] = True

        tasks = plan_data.get("tasks")

        if tasks is None:
            checks["tasks_present"] = False
            return

        if not isinstance(tasks, list):
            risks.append("tasks_not_list")
            checks["tasks_present"] = False
            return

        checks["tasks_present"] = True
        checks["tasks_nonempty"] = bool(tasks)

        if not tasks:
            warnings.append("empty_task_plan")
            return

        task_ids = []
        active_count = 0

        for index, task in enumerate(tasks):
            if not isinstance(task, dict):
                risks.append(
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
            risks.append("duplicate_task_ids")

        if active_count > 1:
            risks.append("multiple_active_tasks")

    # =========================================================
    # RESULT RISK
    # =========================================================

    def _check_result(
        self,
        result: Any,
        risks: List[str],
        warnings: List[str],
        checks: Dict[str, bool],
    ) -> None:
        if result is None:
            warnings.append("missing_result")
            checks["result_present"] = False
            return

        result_data = self._as_dict(result)

        if not result_data:
            risks.append("unreadable_result")
            checks["result_present"] = False
            return

        checks["result_present"] = True

        success = result_data.get("success")

        if success is not None:
            if not isinstance(success, bool):
                risks.append("invalid_success_type")
                checks["success_type_valid"] = False
            else:
                checks["success_type_valid"] = True

        verification = result_data.get(
            "verification"
        )

        if verification is not None:
            if not isinstance(
                verification,
                dict,
            ):
                risks.append(
                    "invalid_verification"
                )
                checks[
                    "verification_valid"
                ] = False
            else:
                checks[
                    "verification_valid"
                ] = True

                verified = verification.get(
                    "verified"
                )

                verification_success = (
                    verification.get("success")
                )

                if (
                    verified is True
                    and verification_success is False
                ):
                    risks.append(
                        "verification_conflict"
                    )

    # =========================================================
    # CONSISTENCY RISK
    # =========================================================

    def _check_consistency(
        self,
        goal: Any,
        result: Any,
        risks: List[str],
        warnings: List[str],
        checks: Dict[str, bool],
    ) -> None:
        goal_data = self._as_dict(goal)
        result_data = self._as_dict(result)

        if not goal_data or not result_data:
            checks["goal_result_consistent"] = False
            return

        goal_target = self._text(
            goal_data.get("target")
        ).lower()

        result_target = self._text(
            result_data.get("target")
        ).lower()

        if (
            goal_target
            and result_target
            and goal_target != result_target
        ):
            risks.append(
                "goal_result_target_mismatch"
            )
            checks[
                "goal_result_consistent"
            ] = False
        else:
            checks[
                "goal_result_consistent"
            ] = True

    # =========================================================
    # RISK LEVEL
    # =========================================================

    @staticmethod
    def _risk_level(
        risks: List[str],
        warnings: List[str],
    ) -> str:
        critical = {
            "goal_result_target_mismatch",
            "verification_conflict",
            "unreadable_goal",
            "unreadable_result",
        }

        high = {
            "tasks_not_list",
            "duplicate_task_ids",
            "multiple_active_tasks",
            "invalid_success_type",
            "invalid_verification",
        }

        if any(item in critical for item in risks):
            return "critical"

        if any(item in high for item in risks):
            return "high"

        if risks:
            return "medium"

        if warnings:
            return "low"

        return "low"

    # =========================================================
    # VERDICT
    # =========================================================

    @staticmethod
    def _verdict(
        level: str,
        risks: List[str],
        warnings: List[str],
    ) -> str:
        blocking = {
            "goal_result_target_mismatch",
            "verification_conflict",
            "unreadable_goal",
            "unreadable_result",
            "tasks_not_list",
            "duplicate_task_ids",
            "multiple_active_tasks",
            "invalid_success_type",
            "invalid_verification",
        }

        if any(item in blocking for item in risks):
            return "block"

        if risks or warnings:
            return "review"

        return "pass"

    # =========================================================
    # MITIGATION
    # =========================================================

    @staticmethod
    def _mitigation(
        risks: List[str],
        warnings: List[str],
    ) -> List[str]:
        actions: List[str] = []

        mapping = {
            "missing_goal":
                "Clarify the goal before execution.",
            "empty_goal_text":
                "Clarify the intended goal.",
            "action_without_target":
                "Resolve the target before executing the action.",
            "tasks_not_list":
                "Rebuild the task plan with a valid task list.",
            "duplicate_task_ids":
                "Regenerate unique task identifiers.",
            "multiple_active_tasks":
                "Allow only one active task at a time.",
            "invalid_success_type":
                "Normalize execution success to a boolean.",
            "invalid_verification":
                "Repair the verification structure.",
            "verification_conflict":
                "Reconcile execution and verification results.",
            "goal_result_target_mismatch":
                "Reconcile the goal target with the execution result.",
            "unreadable_goal":
                "Normalize the goal object before evaluation.",
            "unreadable_result":
                "Normalize the execution result before evaluation.",
        }

        for item in risks + warnings:
            action = mapping.get(item)

            if action and action not in actions:
                actions.append(action)

        return actions

    # =========================================================
    # SCORE
    # =========================================================

    @staticmethod
    def _score(
        level: str,
        verdict: str,
        risks: List[str],
        warnings: List[str],
    ) -> float:
        score = 1.0

        score -= min(
            0.20 * len(risks),
            0.80,
        )

        score -= min(
            0.05 * len(warnings),
            0.30,
        )

        if level == "medium":
            score = min(score, 0.65)

        elif level == "high":
            score = min(score, 0.40)

        elif level == "critical":
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

    def evaluate(
        self,
        goal: Any = None,
        plan: Any = None,
        result: Any = None,
    ) -> Dict[str, Any]:
        risks: List[str] = []
        warnings: List[str] = []
        checks: Dict[str, bool] = {}

        self._check_goal(
            goal,
            risks,
            warnings,
            checks,
        )

        self._check_plan(
            plan,
            risks,
            warnings,
            checks,
        )

        self._check_result(
            result,
            risks,
            warnings,
            checks,
        )

        self._check_consistency(
            goal,
            result,
            risks,
            warnings,
            checks,
        )

        level = self._risk_level(
            risks,
            warnings,
        )

        verdict = self._verdict(
            level,
            risks,
            warnings,
        )

        score = self._score(
            level,
            verdict,
            risks,
            warnings,
        )

        mitigation = self._mitigation(
            risks,
            warnings,
        )

        if verdict == "pass":
            reason = "No material risk detected."

        elif verdict == "review":
            reason = "Potential risk requires review."

        else:
            reason = "Blocking risk detected."

        result_data = {
            "verdict": verdict,
            "valid": True,
            "risk_level": level,
            "score": score,
            "risks": list(risks),
            "warnings": list(warnings),
            "checks": dict(checks),
            "mitigation": mitigation,
            "goal": goal,
            "plan": plan,
            "result": result,
            "reason": reason,
            "version": self.VERSION,
        }

        self.last_result = result_data

        return result_data

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
            == "P10-1.0",
            "levels": self.VALID_LEVELS
            == {
                "low",
                "medium",
                "high",
                "critical",
            },
            "verdicts": self.VALID_VERDICTS
            == {
                "pass",
                "review",
                "block",
            },
            "evaluate_callable": callable(
                self.evaluate
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
            "last_result": self.last_result,
            "has_result": self.last_result is not None,
        }


def create_risk() -> Risk:
    return Risk()


def self_check() -> Dict[str, Any]:
    risk = Risk()

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

    evaluated = risk.evaluate(
        goal=goal,
        plan=plan,
        result=result,
    )

    checks = {
        "validate":
            risk.validate().get("valid") is True,
        "result_valid":
            evaluated.get("valid") is True,
        "verdict":
            evaluated.get("verdict") in
            Risk.VALID_VERDICTS,
        "risk_level":
            evaluated.get("risk_level") in
            Risk.VALID_LEVELS,
        "score":
            isinstance(
                evaluated.get("score"),
                float,
            ),
        "mitigation":
            isinstance(
                evaluated.get("mitigation"),
                list,
            ),
    }

    return {
        "valid": all(checks.values()),
        "checks": checks,
        "result": evaluated,
        "version": Risk.VERSION,
    }
