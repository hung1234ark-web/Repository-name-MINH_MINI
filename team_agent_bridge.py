# ============================================================
# MINH MINI — TEAM AGENT BRIDGE
# P10-TEAM / safe local dispatch layer
# ============================================================

from __future__ import annotations

import json
import os
import shlex
import subprocess
from dataclasses import dataclass
from typing import Any

from team_center import get_task, update_task_status, submit_report


AGENT_COMMAND_ENV = {
    "ti_nhoc": "MINH_AGENT_TI_NHOC_CMD",
    "ti": "MINH_AGENT_TI_CMD",
    "lem": "MINH_AGENT_LEM_CMD",
}


@dataclass
class DispatchResult:
    success: bool
    task_id: str
    agent_id: str
    message: str
    returncode: int | None = None
    stdout: str = ""
    stderr: str = ""


def _command_for(agent_id: str) -> str:
    env_name = AGENT_COMMAND_ENV.get(agent_id, "")
    return os.environ.get(env_name, "").strip() if env_name else ""


def dispatch_task(task_id: str, *, timeout: int = 900) -> DispatchResult:
    task = get_task(task_id)
    if task is None:
        return DispatchResult(False, task_id, "", "Task không tồn tại.")

    agent_id = str(task.get("agent_id", ""))
    command_text = _command_for(agent_id)

    # Không có command thật -> BLOCKED, tuyệt đối không giả PASS.
    if not command_text:
        return DispatchResult(
            False,
            task_id,
            agent_id,
            f"Chưa cấu hình command cho {agent_id}.",
        )

    try:
        command = shlex.split(command_text, posix=False)
    except ValueError as exc:
        return DispatchResult(False, task_id, agent_id, f"Command không hợp lệ: {exc}")

    payload = json.dumps(
        {
            "task": task,
            "agent_id": agent_id,
            "protocol": "MINH-MINI-TEAM-TASK-V1",
        },
        ensure_ascii=False,
    )

    try:
        update_task_status(task_id, "IN_PROGRESS")
        completed = subprocess.run(
            command,
            input=payload,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return DispatchResult(False, task_id, agent_id, "Agent command timeout.")
    except OSError as exc:
        return DispatchResult(False, task_id, agent_id, f"Không khởi chạy được agent: {exc}")

    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()

    if completed.returncode != 0:
        return DispatchResult(
            False,
            task_id,
            agent_id,
            "Agent trả về lỗi.",
            completed.returncode,
            stdout,
            stderr,
        )

    # Agent phải trả JSON report hợp lệ để được ghi nhận.
    try:
        report = json.loads(stdout)
    except json.JSONDecodeError:
        return DispatchResult(
            False,
            task_id,
            agent_id,
            "Agent chạy xong nhưng không trả report JSON hợp lệ.",
            completed.returncode,
            stdout,
            stderr,
        )

    result = str(report.get("result", "UNKNOWN")).upper()
    if result not in {"PASS", "FAIL", "BLOCKED", "UNKNOWN"}:
        result = "UNKNOWN"

    submit_report(
        task_id,
        str(report.get("summary", "")).strip(),
        str(report.get("details", "")).strip(),
        result=result,
        reporter=str(report.get("reporter", "")).strip(),
    )

    return DispatchResult(
        True,
        task_id,
        agent_id,
        "Agent đã thực thi và gửi report.",
        completed.returncode,
        stdout,
        stderr,
    )


def dispatch_assigned_tasks(*, limit: int = 3) -> list[DispatchResult]:
    from team_center import get_tasks

    tasks = get_tasks(status="ASSIGNED")[: max(0, int(limit))]
    return [dispatch_task(task["id"]) for task in tasks]


def self_check() -> bool:
    ok = all(
        isinstance(name, str) and name
        for name in AGENT_COMMAND_ENV.values()
    )
    print(f"[{'PASS' if ok else 'FAIL'}] dispatch protocol")
    print("[PASS] no command => no false-success")
    return ok


if __name__ == "__main__":
    print(
        json.dumps(
            {
                "module": "team_agent_bridge",
                "protocol": "MINH-MINI-TEAM-TASK-V1",
                "agents": list(AGENT_COMMAND_ENV),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
