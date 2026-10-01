import json
import tempfile
from pathlib import Path

import team_center


def main():
    original_dir = team_center.TEAM_DIR
    original_tasks = team_center.TASKS_FILE
    original_reports = team_center.REPORTS_FILE

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        team_center.TEAM_DIR = root / "team"
        team_center.TASKS_FILE = team_center.TEAM_DIR / "tasks.json"
        team_center.REPORTS_FILE = team_center.TEAM_DIR / "reports.json"

        task = team_center.create_task(
            "ti_nhoc",
            "QA smoke task",
            "Find one known test issue.",
        )
        assert task["status"] == "ASSIGNED"

        team_center.update_task_status(task["id"], "IN_PROGRESS")
        report = team_center.submit_report(
            task["id"],
            "Smoke test complete.",
            result="PASS",
        )

        assert report["task_id"] == task["id"]
        assert team_center.get_task(task["id"])["status"] == "REPORT_SUBMITTED"

        dashboard = team_center.get_dashboard()
        assert dashboard["task_counts"]["REPORT_SUBMITTED"] == 1

        print(">>> P10-TEAM-01 SELF TEST: PASS")

    team_center.TEAM_DIR = original_dir
    team_center.TASKS_FILE = original_tasks
    team_center.REPORTS_FILE = original_reports


if __name__ == "__main__":
    main()
