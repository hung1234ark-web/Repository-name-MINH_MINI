import os
import time
from datetime import datetime

REMOTE = "origin"
BRANCH = "main"
INTERVAL = 1
SHOW_COMMITS = 8
STATUS_FILE = os.path.join(os.path.dirname(__file__), "minh_live_status.txt")

def read_status():
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "Minh chưa ghi trạng thái công việc."

def run_git(*args):
    import subprocess
    result = subprocess.run(
        ["git", *args], capture_output=True, text=True,
        timeout=15, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()

def snapshot():
    run_git("fetch", REMOTE, BRANCH, "--quiet")
    head = run_git("rev-parse", f"{REMOTE}/{BRANCH}")
    log = run_git("log", f"-{SHOW_COMMITS}", "--date=iso",
                  "--pretty=format:%h%x09%ad%x09%s", f"{REMOTE}/{BRANCH}")
    items = [line.split("\t", 2) for line in log.splitlines() if line.strip()]
    return head, items

def render(head, items):
    os.system("cls")
    print("=" * 68)
    print("             MINH MINI - LIVE WORK CONSOLE")
    print("=" * 68)
    print(f"TIME   : {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %z')}")
    print(f"HEAD   : {head[:12]}")
    print()
    print("TRANG THAI MINH:")
    print(read_status())
    print()
    print("-" * 68)
    print("GITHUB - 8 COMMIT GAN NHAT")
    for row in items:
        if len(row) == 3:
            print(f"  [{row[0]}] {row[1]}  {row[2]}")
    print()
    print("Console tu dong cap nhat moi 1 giay.")
    print("Nhan Ctrl+C de thoat.")

def main():
    previous = None
    while True:
        try:
            head, items = snapshot()
            status = read_status()
            signature = head + status
            if signature != previous:
                render(head, items)
                previous = signature
        except KeyboardInterrupt:
            print("\nDa thoat MINH LIVE.")
            break
        except Exception as exc:
            os.system("cls")
            print("MINH MINI - LIVE WORK CONSOLE")
            print(f"[MONITOR ERROR] {exc}")
            print()
            print("Dang cho ket noi lai...")
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
