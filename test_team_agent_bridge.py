from __future__ import annotations

import os
import tempfile
from pathlib import Path

import team_center
import team_agent_bridge


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        old_team_dir = team_center.TEAM_DIR
        old_tasks = team_center.TASKS_FILE
        old_reports = team_center.REPORTS_FILE

        try:
            team_center.TEAM_DIR = root
            team_center.TASKS_FILE = root / "tasks.json"
            team_center.REPORTS_FILE = root / "reports.json"

            task = team_center.create_task(
                "ti_nhoc",
                "bridge test",
                "Verify dispatch does not claim success without a configured agent.",
            )

            old = os.environ.pop("MINH_AGENT_TI_NHOC_CMD", None)
            try:
                result = team_agent_bridge.dispatch_task(task["id"])
                assert result.success is False
                assert "Chưa cấu hình command" in result.message
                assert team_center.get_task(task["id"])["status"] == "ASSIGNED"
            finally:
                if old is not None:
                    os.environ["MINH_AGENT_TI_NHOC_CMD"] = old
        finally:
            team_center.TEAM_DIR = old_team_dir
            team_center.TASKS_FILE = old_tasks
            team_center.REPORTS_FILE = old_reports

    print(">>> P10-TEAM AGENT BRIDGE SELF TEST: PASS")


if __name__ == "__main__":
    main()
