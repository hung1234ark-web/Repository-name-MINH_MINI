# ============================================================
# MINH MINI — TEAM CENTER LAUNCHER
# P10-TEAM
# ============================================================

from __future__ import annotations

import argparse
import threading
import time
import urllib.request

from team_agent_bridge import dispatch_assigned_tasks


def _dispatch_loop(interval: int) -> None:
    while True:
        try:
            dispatch_assigned_tasks(limit=3)
        except Exception as exc:
            # Launcher must stay alive; failed dispatch is not success.
            print(f"[TEAM DISPATCH ERROR] {exc}")
        time.sleep(max(2, interval))


def start(host: str = "127.0.0.1", port: int = 8765, interval: int = 5) -> None:
    from team_center_web import run_server

    worker = threading.Thread(
        target=_dispatch_loop,
        args=(interval,),
        daemon=True,
        name="team-dispatcher",
    )
    worker.start()

    print("MINH MINI TEAM CENTER")
    print(f"UI: http://{host}:{port}")
    print("Dispatcher: ACTIVE")
    print("Auto-success: DISABLED")

    run_server(host=host, port=port)


def main() -> None:
    parser = argparse.ArgumentParser(description="MINH MINI Team Center")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--interval", type=int, default=5)
    args = parser.parse_args()

    start(args.host, args.port, args.interval)


if __name__ == "__main__":
    main()
