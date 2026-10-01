import subprocess
import time
from datetime import datetime

REMOTE = "origin"
BRANCH = "main"
INTERVAL = 3
SHOW_COMMITS = 8

def run_git(*args):
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        timeout=15,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()

def remote_head():
    output = run_git("ls-remote", REMOTE, f"refs/heads/{BRANCH}")
    if not output:
        raise RuntimeError("remote branch not found")
    return output.split()[0]

def update_remote_ref():
    run_git("fetch", REMOTE, BRANCH, "--quiet")
    return run_git("rev-parse", f"{REMOTE}/{BRANCH}")

def snapshot():
    head = update_remote_ref()
    log = run_git(
        "log",
        f"-{SHOW_COMMITS}",
        "--date=iso",
        "--pretty=format:%h%x09%ad%x09%s",
        f"{REMOTE}/{BRANCH}",
    )
    items = []
    for line in log.splitlines():
        sha, date, msg = line.split("\t", 2)
        items.append((sha, date, msg))
    return head, items

def render(head, items):
    print("\033[2J\033[H", end="")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║              MINH MINI — LIVE WORK MONITOR             ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"Remote : {REMOTE}")
    print(f"Branch : {BRANCH}")
    print(f"Poll   : every {INTERVAL}s")
    print(f"Time   : {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %z')}")
    print(f"HEAD   : {head[:12]}")
    print()
    print("THAY ĐỔI THẬT TRÊN GITHUB (commit mới nhất trước):")
    for sha, date, msg in items:
        print(f"  [{sha}] {date}  {msg}")
    print()
    print("Monitor dùng Git để theo dõi remote branch, không gọi GitHub REST API.")
    print("Vì vậy không bị GitHub API rate limit 403 như bản cũ.")
    print("Nó KHÔNG giả lập thao tác gõ code và KHÔNG hiển thị suy nghĩ nội bộ.")
    print()
    print("Ctrl+C để thoát.")

def main():
    previous_head = None
    while True:
        try:
            head, items = snapshot()
            if head != previous_head:
                render(head, items)
                previous_head = head
        except Exception as e:
            print(f"\n[MONITOR ERROR] {e}")
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
