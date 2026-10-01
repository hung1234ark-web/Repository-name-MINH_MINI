# ============================================================
# MINH MINI — TEAM CENTER
# P10-TEAM-01 / Team task + report backend
# ============================================================

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
import json
import threading
import uuid


APP_DIR = Path(__file__).resolve().parent
TEAM_DIR = APP_DIR / "team_center_data"
TASKS_FILE = TEAM_DIR / "tasks.json"
REPORTS_FILE = TEAM_DIR / "reports.json"
LOCK = threading.RLock()

AGENTS = {
    "ti_nhoc": {
        "id": "ti_nhoc",
        "name": "Tì Nhóc",
        "role": "Bug Hunter",
        "scope": "Find bugs, logic/runtime/regression/false-success issues. Do not fix code.",
    },
    "ti": {
        "id": "ti",
        "name": "Tì",
        "role": "Fixer AI",
        "scope": "Fix confirmed bugs within assigned scope. Do not hunt independently or upgrade.",
    },
    "lem": {
        "id": "lem",
        "name": "Lem",
        "role": "QA / Test Engineer",
        "scope": "Independently test and verify fixes. Do not modify production code.",
    },
}

VALID_STATUSES = {
    "DRAFT",
    "ASSIGNED",
    "IN_PROGRESS",
    "REPORT_SUBMITTED",
    "MINH_REVIEW",
    "VERIFY",
    "DONE",
    "REWORK",
    "CANCELLED",
}


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _ensure_files() -> None:
    TEAM_DIR.mkdir(parents=True, exist_ok=True)
    if not TASKS_FILE.exists():
        TASKS_FILE.write_text("[]", encoding="utf-8")
    if not REPORTS_FILE.exists():
        REPORTS_FILE.write_text("[]", encoding="utf-8")


def _read(path: Path) -> list[dict[str, Any]]:
    _ensure_files()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _write(path: Path, data: list[dict[str, Any]]) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def list_agents() -> list[dict[str, Any]]:
    with LOCK:
        tasks = _read(TASKS_FILE)
        result = []
        for agent in AGENTS.values():
            active = [
                t for t in tasks
                if t.get("agent_id") == agent["id"]
                and t.get("status") not in {"DONE", "CANCELLED"}
            ]
            result.append({
                **agent,
                "active_tasks": len(active),
            })
        return result


def create_task(
    agent_id: str,
    title: str,
    description: str,
    *,
    priority: str = "NORMAL",
    created_by: str = "Minh",
    task_id: str | None = None,
) -> dict[str, Any]:
    if agent_id not in AGENTS:
        raise ValueError("agent_id không hợp lệ.")
    title = str(title or "").strip()
    description = str(description or "").strip()
    if not title:
        raise ValueError("Task phải có title.")
    if not description:
        raise ValueError("Task phải có description.")

    with LOCK:
        tasks = _read(TASKS_FILE)
        task = {
            "id": task_id or ("TASK-" + uuid.uuid4().hex[:8].upper()),
            "agent_id": agent_id,
            "agent_name": AGENTS[agent_id]["name"],
            "title": title,
            "description": description,
            "priority": str(priority or "NORMAL").upper(),
            "status": "ASSIGNED",
            "created_by": created_by,
            "created_at": _now(),
            "updated_at": _now(),
            "started_at": None,
            "completed_at": None,
            "report_ids": [],
        }
        tasks.append(task)
        _write(TASKS_FILE, tasks)
        return task


def get_tasks(
    *,
    agent_id: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    with LOCK:
        tasks = _read(TASKS_FILE)
        if agent_id:
            tasks = [t for t in tasks if t.get("agent_id") == agent_id]
        if status:
            tasks = [t for t in tasks if t.get("status") == status]
        return list(reversed(tasks))


def get_task(task_id: str) -> dict[str, Any] | None:
    with LOCK:
        for task in _read(TASKS_FILE):
            if task.get("id") == task_id:
                return task
    return None


def update_task_status(task_id: str, status: str) -> dict[str, Any]:
    status = str(status or "").upper()
    if status not in VALID_STATUSES:
        raise ValueError("status không hợp lệ.")

    with LOCK:
        tasks = _read(TASKS_FILE)
        for task in tasks:
            if task.get("id") == task_id:
                old = task.get("status")
                task["status"] = status
                task["updated_at"] = _now()
                if status == "IN_PROGRESS" and not task.get("started_at"):
                    task["started_at"] = _now()
                if status == "DONE":
                    task["completed_at"] = _now()
                _write(TASKS_FILE, tasks)
                return {"task": task, "previous_status": old}
    raise KeyError("Không tìm thấy task.")


def submit_report(
    task_id: str,
    summary: str,
    details: str = "",
    *,
    result: str = "UNKNOWN",
    reporter: str = "",
) -> dict[str, Any]:
    result = str(result or "UNKNOWN").upper()
    if result not in {"PASS", "FAIL", "BLOCKED", "UNKNOWN"}:
        raise ValueError("result phải là PASS/FAIL/BLOCKED/UNKNOWN.")

    with LOCK:
        tasks = _read(TASKS_FILE)
        task = next((t for t in tasks if t.get("id") == task_id), None)
        if task is None:
            raise KeyError("Không tìm thấy task.")

        reports = _read(REPORTS_FILE)
        report = {
            "id": "REPORT-" + uuid.uuid4().hex[:8].upper(),
            "task_id": task_id,
            "agent_id": task.get("agent_id", ""),
            "agent_name": task.get("agent_name", ""),
            "reporter": reporter or task.get("agent_name", ""),
            "summary": str(summary or "").strip(),
            "details": str(details or "").strip(),
            "result": result,
            "created_at": _now(),
        }
        reports.append(report)

        task["status"] = "REPORT_SUBMITTED"
        task["updated_at"] = _now()
        task.setdefault("report_ids", []).append(report["id"])

        _write(REPORTS_FILE, reports)
        _write(TASKS_FILE, tasks)
        return report


def get_reports(*, task_id: str | None = None) -> list[dict[str, Any]]:
    with LOCK:
        reports = _read(REPORTS_FILE)
        if task_id:
            reports = [r for r in reports if r.get("task_id") == task_id]
        return list(reversed(reports))


def get_dashboard() -> dict[str, Any]:
    with LOCK:
        tasks = _read(TASKS_FILE)
        reports = _read(REPORTS_FILE)
        counts = {status: 0 for status in sorted(VALID_STATUSES)}
        for task in tasks:
            status = task.get("status")
            if status in counts:
                counts[status] += 1
        return {
            "agents": list_agents(),
            "task_counts": counts,
            "tasks": list(reversed(tasks))[:50],
            "reports": list(reversed(reports))[:50],
            "updated_at": _now(),
        }


def self_check() -> bool:
    _ensure_files()
    checks = [
        ("agents", bool(AGENTS)),
        ("task_file", TASKS_FILE.exists()),
        ("report_file", REPORTS_FILE.exists()),
        ("create_task", callable(create_task)),
        ("submit_report", callable(submit_report)),
        ("dashboard", callable(get_dashboard)),
    ]
    for name, ok in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    return all(ok for _, ok in checks)


if __name__ == "__main__":
    print(">>> TEAM CENTER SELF CHECK:", "PASS" if self_check() else "FAIL")
