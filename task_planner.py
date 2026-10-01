from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional


class TaskPlanner:
    """
    P7-1.0 — Task Planner Core

    Responsibility:
    - Convert a goal into an ordered task plan.
    - Track task status.
    - Read/update task state safely.
    - Provide isolated snapshots.
    - Validate planner state.

    Explicit non-responsibilities:
    - No execution.
    - No routing.
    - No Ollama.
    - No Web.
    - No Action.
    - No Tool Selector.
    - No World Model mutation.
    - No State Manager mutation.
    """

    VERSION = "P7-1.0"

    VALID_STATUSES = {
        "planned",
        "active",
        "completed",
        "blocked",
        "failed",
    }

    def __init__(
        self,
        goal: Optional[Dict[str, Any]] = None,
        tasks: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.goal: Optional[Dict[str, Any]] = (
            deepcopy(goal) if isinstance(goal, dict) else None
        )

        self.tasks: List[Dict[str, Any]] = (
            deepcopy(tasks) if isinstance(tasks, list) else []
        )

        self.current_task_index: Optional[int] = None
        self.last_update: str = self._timestamp()

    # ---------------------------------------------------------
    # INTERNAL
    # ---------------------------------------------------------

    @staticmethod
    def _timestamp() -> str:
        return datetime.now().isoformat()

    def _touch(self) -> None:
        self.last_update = self._timestamp()

    # ---------------------------------------------------------
    # GOAL
    # ---------------------------------------------------------

    def set_goal(self, goal: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if goal is None:
            self.goal = None
        elif isinstance(goal, dict):
            self.goal = deepcopy(goal)
        else:
            raise TypeError("goal must be a dict or None")

        self._touch()

        return {
            "goal": deepcopy(self.goal),
            "updated": True,
        }

    def get_goal(self) -> Optional[Dict[str, Any]]:
        return deepcopy(self.goal)

    # ---------------------------------------------------------
    # TASK CREATION
    # ---------------------------------------------------------

    def add_task(
        self,
        description: str,
        task_id: Optional[str] = None,
        status: str = "planned",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not isinstance(description, str) or not description.strip():
            raise ValueError("description must be a non-empty string")

        if status not in self.VALID_STATUSES:
            raise ValueError(f"invalid task status: {status}")

        if task_id is None:
            task_id = f"task_{len(self.tasks) + 1}"

        task = {
            "id": str(task_id),
            "description": description.strip(),
            "status": status,
            "metadata": deepcopy(metadata) if isinstance(metadata, dict) else {},
        }

        self.tasks.append(task)

        if self.current_task_index is None and status in {
            "planned",
            "active",
        }:
            self.current_task_index = len(self.tasks) - 1

        self._touch()

        return deepcopy(task)

    # ---------------------------------------------------------
    # PLAN CREATION
    # ---------------------------------------------------------

    def create_plan(
        self,
        goal: Dict[str, Any],
        task_descriptions: List[str],
    ) -> Dict[str, Any]:
        if not isinstance(goal, dict):
            raise TypeError("goal must be a dict")

        if not isinstance(task_descriptions, list):
            raise TypeError("task_descriptions must be a list")

        self.goal = deepcopy(goal)
        self.tasks = []
        self.current_task_index = None

        for description in task_descriptions:
            self.add_task(description)

        self._touch()

        return self.get_plan()

    # ---------------------------------------------------------
    # TASK ACCESS
    # ---------------------------------------------------------

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        for task in self.tasks:
            if task.get("id") == task_id:
                return deepcopy(task)

        return None

    def get_tasks(self) -> List[Dict[str, Any]]:
        return deepcopy(self.tasks)

    def get_current_task(self) -> Optional[Dict[str, Any]]:
        if self.current_task_index is None:
            return None

        if not (
            0 <= self.current_task_index < len(self.tasks)
        ):
            return None

        return deepcopy(self.tasks[self.current_task_index])

    # ---------------------------------------------------------
    # TASK STATUS
    # ---------------------------------------------------------

    def update_task_status(
        self,
        task_id: str,
        status: str,
    ) -> Dict[str, Any]:
        if status not in self.VALID_STATUSES:
            raise ValueError(f"invalid task status: {status}")

        for index, task in enumerate(self.tasks):
            if task.get("id") == task_id:
                task["status"] = status

                if status == "active":
                    self.current_task_index = index

                elif (
                    index == self.current_task_index
                    and status in {
                        "completed",
                        "blocked",
                        "failed",
                    }
                ):
                    self._select_next_planned_task()

                self._touch()

                return deepcopy(task)

        raise KeyError(f"task not found: {task_id}")

    def _select_next_planned_task(self) -> None:
        for index, task in enumerate(self.tasks):
            if task.get("status") == "planned":
                self.current_task_index = index
                return

        self.current_task_index = None

    # ---------------------------------------------------------
    # PLAN STATE
    # ---------------------------------------------------------

    def get_plan(self) -> Dict[str, Any]:
        return {
            "version": self.VERSION,
            "goal": deepcopy(self.goal),
            "tasks": deepcopy(self.tasks),
            "current_task_index": self.current_task_index,
            "current_task": self.get_current_task(),
            "last_update": self.last_update,
        }

    def snapshot(self) -> Dict[str, Any]:
        return deepcopy(self.get_plan())

    # ---------------------------------------------------------
    # RESET
    # ---------------------------------------------------------

    def reset(self) -> Dict[str, Any]:
        self.goal = None
        self.tasks = []
        self.current_task_index = None
        self._touch()

        return self.get_plan()

    # ---------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------

    def validate(self) -> Dict[str, Any]:
        errors: List[str] = []

        if not isinstance(self.tasks, list):
            errors.append("tasks_not_list")

        if self.goal is not None and not isinstance(self.goal, dict):
            errors.append("goal_not_dict")

        task_ids = set()

        for task in self.tasks:
            if not isinstance(task, dict):
                errors.append("task_not_dict")
                continue

            task_id = task.get("id")
            description = task.get("description")
            status = task.get("status")

            if not task_id:
                errors.append("task_missing_id")
            elif task_id in task_ids:
                errors.append(f"duplicate_task_id:{task_id}")
            else:
                task_ids.add(task_id)

            if not isinstance(description, str) or not description.strip():
                errors.append(f"task_invalid_description:{task_id}")

            if status not in self.VALID_STATUSES:
                errors.append(f"task_invalid_status:{task_id}")

        if self.current_task_index is not None:
            if not isinstance(self.current_task_index, int):
                errors.append("current_task_index_not_int")
            elif not (
                0 <= self.current_task_index < len(self.tasks)
            ):
                errors.append("current_task_index_out_of_range")

        return {
            "valid": not errors,
            "errors": errors,
            "task_count": len(self.tasks),
            "has_goal": self.goal is not None,
            "current_task_index": self.current_task_index,
            "version": self.VERSION,
        }

    # ---------------------------------------------------------
    # STATUS
    # ---------------------------------------------------------

    def status(self) -> Dict[str, Any]:
        validation = self.validate()

        return {
            "module": "task_planner",
            "version": self.VERSION,
            "goal_present": self.goal is not None,
            "task_count": len(self.tasks),
            "current_task_index": self.current_task_index,
            "current_task": self.get_current_task(),
            "valid": validation["valid"],
            "errors": validation["errors"],
        }


def create_task_planner(
    goal: Optional[Dict[str, Any]] = None,
    tasks: Optional[List[Dict[str, Any]]] = None,
) -> TaskPlanner:
    return TaskPlanner(goal=goal, tasks=tasks)


def self_check() -> Dict[str, Any]:
    planner = TaskPlanner()

    goal = {
        "text": "Mở YouTube rồi tìm Python",
        "intent": "action",
    }

    planner.set_goal(goal)

    planner.add_task("Mở YouTube")
    planner.add_task("Tìm Python")

    validation = planner.validate()

    return {
        "version": TaskPlanner.VERSION,
        "valid": validation["valid"],
        "task_count": len(planner.tasks),
        "current_task": planner.get_current_task(),
    }