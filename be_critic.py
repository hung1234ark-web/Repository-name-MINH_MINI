from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional


class BECritic:
    """
    MINH MINI P8-1.0 — BE Critic Core

    Nhiệm vụ:
    - Đánh giá Goal.
    - Đánh giá Task Plan.
    - Phát hiện thiếu thông tin cơ bản.
    - Phát hiện task không hợp lệ.
    - Phát hiện trạng thái mâu thuẫn.
    - Đưa ra verdict: pass / review / block.

    Không:
    - execute
    - route
    - gọi Ollama
    - gọi Web
    - gọi Action
    - sửa World Model
    - sửa State Manager
    """

    VERSION = "P8-1.0"

    VALID_VERDICTS = {
        "pass",
        "review",
        "block",
    }

    VALID_TASK_STATUSES = {
        "planned",
        "active",
        "completed",
        "blocked",
        "failed",
    }

    def __init__(
        self,
        strict: bool = True,
    ) -> None:
        self.strict = bool(strict)

        self.last_result: Optional[Dict[str, Any]] = None

    # ========================================================
    # PUBLIC API
    # ========================================================

    def evaluate(
        self,
        goal: Any = None,
        plan: Any = None,
    ) -> Dict[str, Any]:
        """
        Đánh giá goal + task plan.

        Kết quả:
        {
            "verdict": "pass|review|block",
            "valid": bool,
            "score": float,
            "issues": [...],
            "warnings": [...],
            "checks": {...},
            "goal": {...},
            "plan": {...},
            "reason": str,
            "version": str,
        }
        """

        issues: List[str] = []
        warnings: List[str] = []

        checks: Dict[str, bool] = {
            "goal_present": False,
            "goal_valid": False,
            "plan_valid": True,
            "tasks_valid": True,
            "task_statuses_valid": True,
            "current_task_valid": True,
            "no_conflicting_tasks": True,
        }

        normalized_goal = self._normalize_goal(goal)
        normalized_plan = self._normalize_plan(plan)

        # ----------------------------------------------------
        # GOAL
        # ----------------------------------------------------

        if normalized_goal is None:
            issues.append("missing_goal")
        else:
            checks["goal_present"] = True

            goal_valid, goal_issues = self._validate_goal(
                normalized_goal
            )

            checks["goal_valid"] = goal_valid
            issues.extend(goal_issues)

        # ----------------------------------------------------
        # PLAN
        # ----------------------------------------------------

        if plan is not None:
            plan_valid, plan_issues = self._validate_plan_structure(
                normalized_plan
            )

            checks["plan_valid"] = plan_valid
            issues.extend(plan_issues)

            tasks = normalized_plan.get("tasks", [])

            (
                tasks_valid,
                task_issues,
                status_valid,
                status_issues,
            ) = self._validate_tasks(tasks)

            checks["tasks_valid"] = tasks_valid
            checks["task_statuses_valid"] = status_valid

            issues.extend(task_issues)
            issues.extend(status_issues)

            (
                current_valid,
                current_issues,
            ) = self._validate_current_task(
                normalized_plan
            )

            checks["current_task_valid"] = current_valid
            issues.extend(current_issues)

            (
                conflict_free,
                conflict_issues,
            ) = self._check_task_conflicts(tasks)

            checks["no_conflicting_tasks"] = conflict_free
            issues.extend(conflict_issues)

        # ----------------------------------------------------
        # WARNINGS
        # ----------------------------------------------------

        if normalized_plan is not None:
            tasks = normalized_plan.get("tasks", [])

            if (
                normalized_goal is not None
                and not tasks
            ):
                warnings.append("goal_has_no_tasks")

            if tasks:
                completed_count = sum(
                    1
                    for task in tasks
                    if task.get("status") == "completed"
                )

                if completed_count == len(tasks):
                    warnings.append("all_tasks_completed")

        # ----------------------------------------------------
        # VERDICT
        # ----------------------------------------------------

        verdict = self._determine_verdict(
            issues=issues,
            warnings=warnings,
            checks=checks,
        )

        score = self._calculate_score(
            checks=checks,
            issues=issues,
            warnings=warnings,
        )

        valid = verdict == "pass"

        result = {
            "verdict": verdict,
            "valid": valid,
            "score": score,
            "issues": list(issues),
            "warnings": list(warnings),
            "checks": deepcopy(checks),
            "goal": deepcopy(normalized_goal),
            "plan": deepcopy(normalized_plan),
            "reason": self._build_reason(
                verdict,
                issues,
                warnings,
            ),
            "version": self.VERSION,
        }

        self.last_result = deepcopy(result)

        return result

    def get_last_result(self) -> Optional[Dict[str, Any]]:
        """
        Trả về bản sao kết quả đánh giá gần nhất.
        """

        return deepcopy(self.last_result)

    def reset(self) -> None:
        """
        Xóa kết quả đánh giá trước đó.
        """

        self.last_result = None

    def validate(self) -> Dict[str, Any]:
        """
        Kiểm tra trạng thái nội bộ của Critic.
        """

        valid = (
            isinstance(self.strict, bool)
            and (
                self.last_result is None
                or isinstance(self.last_result, dict)
            )
        )

        return {
            "valid": valid,
            "version": self.VERSION,
            "strict": self.strict,
            "has_result": self.last_result is not None,
        }

    def status(self) -> Dict[str, Any]:
        """
        Trạng thái của BE Critic.
        """

        return {
            "name": "BE Critic",
            "version": self.VERSION,
            "strict": self.strict,
            "has_result": self.last_result is not None,
            "valid": self.validate()["valid"],
        }

    # ========================================================
    # GOAL VALIDATION
    # ========================================================

    def _normalize_goal(
        self,
        goal: Any,
    ) -> Optional[Dict[str, Any]]:
        if goal is None:
            return None

        if isinstance(goal, str):
            text = goal.strip()

            if not text:
                return None

            return {
                "text": text,
            }

        if isinstance(goal, dict):
            return deepcopy(goal)

        return None

    def _validate_goal(
        self,
        goal: Dict[str, Any],
    ) -> tuple[bool, List[str]]:
        issues: List[str] = []

        text = goal.get("text")

        if not isinstance(text, str) or not text.strip():
            issues.append("goal_text_missing")

        if "status" in goal:
            status = goal.get("status")

            if status is not None and not isinstance(status, str):
                issues.append("goal_status_invalid")

        if "steps" in goal:
            steps = goal.get("steps")

            if steps is not None and not isinstance(steps, list):
                issues.append("goal_steps_invalid")

        return (
            len(issues) == 0,
            issues,
        )

    # ========================================================
    # PLAN VALIDATION
    # ========================================================

    def _normalize_plan(
        self,
        plan: Any,
    ) -> Optional[Dict[str, Any]]:
        if plan is None:
            return None

        if not isinstance(plan, dict):
            return {
                "__invalid__": True,
                "raw": deepcopy(plan),
            }

        return deepcopy(plan)

    def _validate_plan_structure(
        self,
        plan: Optional[Dict[str, Any]],
    ) -> tuple[bool, List[str]]:
        issues: List[str] = []

        if plan is None:
            return True, issues

        if plan.get("__invalid__") is True:
            issues.append("plan_not_dict")
            return False, issues

        tasks = plan.get("tasks", [])

        if tasks is None:
            issues.append("plan_tasks_missing")

        elif not isinstance(tasks, list):
            issues.append("plan_tasks_invalid")

        return (
            len(issues) == 0,
            issues,
        )

    # ========================================================
    # TASK VALIDATION
    # ========================================================

    def _validate_tasks(
        self,
        tasks: Any,
    ) -> tuple[
        bool,
        List[str],
        bool,
        List[str],
    ]:
        task_issues: List[str] = []
        status_issues: List[str] = []

        if not isinstance(tasks, list):
            return (
                False,
                ["tasks_not_list"],
                False,
                ["task_statuses_uncheckable"],
            )

        seen_ids = set()

        for index, task in enumerate(tasks):

            if not isinstance(task, dict):
                task_issues.append(
                    f"task_{index}_not_dict"
                )
                continue

            task_id = task.get("id")

            if not isinstance(task_id, str) or not task_id.strip():
                task_issues.append(
                    f"task_{index}_id_missing"
                )
            else:
                if task_id in seen_ids:
                    task_issues.append(
                        f"duplicate_task_id:{task_id}"
                    )

                seen_ids.add(task_id)

            description = task.get("description")

            if (
                not isinstance(description, str)
                or not description.strip()
            ):
                task_issues.append(
                    f"task_{index}_description_missing"
                )

            status = task.get(
                "status",
                "planned",
            )

            if status not in self.VALID_TASK_STATUSES:
                status_issues.append(
                    f"invalid_task_status:{task_id or index}"
                )

        return (
            len(task_issues) == 0,
            task_issues,
            len(status_issues) == 0,
            status_issues,
        )

    # ========================================================
    # CURRENT TASK
    # ========================================================

    def _validate_current_task(
        self,
        plan: Dict[str, Any],
    ) -> tuple[bool, List[str]]:
        issues: List[str] = []

        current_task = plan.get(
            "current_task"
        )

        if current_task is None:
            return True, issues

        tasks = plan.get(
            "tasks",
            [],
        )

        if not isinstance(tasks, list):
            issues.append(
                "current_task_plan_invalid"
            )
            return False, issues

        task_ids = {
            task.get("id")
            for task in tasks
            if isinstance(task, dict)
        }

        current_id = None

        if isinstance(current_task, dict):
            current_id = current_task.get("id")
        elif isinstance(current_task, str):
            current_id = current_task

        if current_id not in task_ids:
            issues.append(
                "current_task_not_in_plan"
            )
            return False, issues

        return True, issues

    # ========================================================
    # CONFLICT DETECTION
    # ========================================================

    def _check_task_conflicts(
        self,
        tasks: Any,
    ) -> tuple[bool, List[str]]:
        issues: List[str] = []

        if not isinstance(tasks, list):
            return False, ["tasks_not_list"]

        active_tasks = [
            task
            for task in tasks
            if isinstance(task, dict)
            and task.get("status") == "active"
        ]

        if len(active_tasks) > 1:
            issues.append(
                "multiple_active_tasks"
            )

        return (
            len(issues) == 0,
            issues,
        )

    # ========================================================
    # VERDICT
    # ========================================================

    def _determine_verdict(
        self,
        issues: List[str],
        warnings: List[str],
        checks: Dict[str, bool],
    ) -> str:

        hard_block_issues = {
            "missing_goal",
            "goal_text_missing",
            "goal_status_invalid",
            "goal_steps_invalid",
            "plan_not_dict",
            "plan_tasks_invalid",
            "tasks_not_list",
            "task_statuses_uncheckable",
            "multiple_active_tasks",
            "current_task_not_in_plan",
        }

        if any(
            issue in hard_block_issues
            for issue in issues
        ):
            return "block"

        if issues:
            return "review"

        if warnings and self.strict:
            return "review"

        return "pass"

    def _calculate_score(
        self,
        checks: Dict[str, bool],
        issues: List[str],
        warnings: List[str],
    ) -> float:

        total = len(checks)

        if total == 0:
            return 0.0

        passed = sum(
            1
            for value in checks.values()
            if value is True
        )

        score = passed / total

        score -= min(
            0.10 * len(issues),
            0.50,
        )

        score -= min(
            0.05 * len(warnings),
            0.25,
        )

        return round(
            max(0.0, min(1.0, score)),
            3,
        )

    # ========================================================
    # REASON
    # ========================================================

    def _build_reason(
        self,
        verdict: str,
        issues: List[str],
        warnings: List[str],
    ) -> str:

        if verdict == "pass":
            return "goal_and_plan_valid"

        if verdict == "block":
            if issues:
                return (
                    "blocking_issues: "
                    + ", ".join(issues)
                )

            return "blocked"

        if issues:
            return (
                "review_required: "
                + ", ".join(issues)
            )

        if warnings:
            return (
                "review_warnings: "
                + ", ".join(warnings)
            )

        return "review_required"


# ============================================================
# FACTORY
# ============================================================

def create_be_critic(
    strict: bool = True,
) -> BECritic:
    return BECritic(
        strict=strict,
    )


# ============================================================
# SELF CHECK
# ============================================================

def self_check() -> Dict[str, Any]:
    critic = create_be_critic()

    valid_goal = {
        "text": "mở youtube",
        "intent": "action",
        "action": "open",
        "target": "youtube",
    }

    valid_plan = {
        "goal": deepcopy(valid_goal),
        "tasks": [
            {
                "id": "task_1",
                "description": "Mở YouTube",
                "status": "planned",
            }
        ],
        "current_task": {
            "id": "task_1",
            "description": "Mở YouTube",
            "status": "planned",
        },
    }

    result = critic.evaluate(
        valid_goal,
        valid_plan,
    )

    if result.get("verdict") != "pass":
        return {
            "valid": False,
            "reason": "valid_case_failed",
            "result": result,
        }

    missing_goal = critic.evaluate(
        None,
        None,
    )

    if missing_goal.get("verdict") != "block":
        return {
            "valid": False,
            "reason": "missing_goal_not_blocked",
            "result": missing_goal,
        }

    invalid_status_plan = {
        "tasks": [
            {
                "id": "task_1",
                "description": "Test",
                "status": "INVALID",
            }
        ]
    }

    invalid_status = critic.evaluate(
        valid_goal,
        invalid_status_plan,
    )

    if invalid_status.get("verdict") != "review":
        return {
            "valid": False,
            "reason": "invalid_status_not_review",
            "result": invalid_status,
        }

    conflict_plan = {
        "tasks": [
            {
                "id": "task_1",
                "description": "Task A",
                "status": "active",
            },
            {
                "id": "task_2",
                "description": "Task B",
                "status": "active",
            },
        ]
    }

    conflict = critic.evaluate(
        valid_goal,
        conflict_plan,
    )

    if conflict.get("verdict") != "block":
        return {
            "valid": False,
            "reason": "conflict_not_blocked",
            "result": conflict,
        }

    validation = critic.validate()

    if validation.get("valid") is not True:
        return {
            "valid": False,
            "reason": "critic_validation_failed",
            "validation": validation,
        }

    return {
        "valid": True,
        "version": BECritic.VERSION,
        "checks": [
            "valid_goal_plan",
            "missing_goal_block",
            "invalid_status_review",
            "conflicting_tasks_block",
            "internal_validation",
        ],
    }


if __name__ == "__main__":
    result = self_check()

    print("=== P8-1 BE CRITIC CORE SELF CHECK ===")
    print("VERSION:", BECritic.VERSION)
    print("VALID:", result.get("valid"))

    if result.get("valid") is True:
        print("P8-1 BE CRITIC CORE: PASS")
    else:
        print("P8-1 BE CRITIC CORE: FAIL")
        print(result)
