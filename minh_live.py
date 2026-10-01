import json
import time
import urllib.request
from datetime import datetime

REPO = "hung1234ark-web/Repository-name-MINH_MINI"
BRANCH = "main"
INTERVAL = 3

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "MINH-MINI-Live-Monitor/1.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))

def snapshot():
    data = fetch_json(f"https://api.github.com/repos/{REPO}/commits?sha={BRANCH}&per_page=8")
    return [(x["sha"][:7], x["commit"]["message"].splitlines()[0], x["commit"]["author"]["date"]) for x in data]

def render(items, first=False):
    print("\033[2J\033[H", end="")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║              MINH MINI — LIVE WORK MONITOR             ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"Repo : {REPO}")
    print(f"Branch: {BRANCH}")
    print(f"Poll : every {INTERVAL}s")
    print(f"Time : {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %z')}")
    print()
    print("THAY ĐỔI THẬT TRÊN GITHUB (commit mới nhất trước):")
    for sha, msg, date in items:
        print(f"  [{sha}] {date}  {msg}")
    print()
    print("Monitor này chỉ hiển thị thay đổi thật đã xuất hiện trên repo.")
    print("Nó KHÔNG giả lập thao tác gõ code và KHÔNG hiển thị suy nghĩ nội bộ.")
    print()
    print("Ctrl+C để thoát.")

def main():
    previous = None
    while True:
        try:
            items = snapshot()
            if items != previous or previous is None:
                render(items, first=previous is None)
                previous = items
        except Exception as e:
            print(f"\n[MONITOR ERROR] {e}")
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
