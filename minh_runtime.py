import subprocess
import sys
import time
from datetime import datetime

INTERVAL = 5
TESTS = [
    ("P13-2 Runtime Validation", "test_p13_2_runtime.py"),
]

def run_test(filename):
    started = time.perf_counter()
    print(f"\n[{datetime.now().astimezone().strftime('%H:%M:%S')}] RUNNING: {filename}")
    print("-" * 64)
    result = subprocess.run(
        [sys.executable, filename],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    elapsed = time.perf_counter() - started
    output = result.stdout.strip()
    error = result.stderr.strip()
    if output:
        print(output)
    if error:
        print("\n[STDERR]")
        print(error)
    status = "PASS" if result.returncode == 0 else "FAIL"
    print("-" * 64)
    print(f"[{datetime.now().astimezone().strftime('%H:%M:%S')}] {filename}: {status} ({elapsed:.2f}s)")
    return result.returncode == 0

def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║            MINH MINI — REAL RUNTIME CONSOLE             ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print("This console runs real repository tests.")
    print("It does NOT simulate execution or expose private reasoning.")
    print(f"Auto-run interval: {INTERVAL}s")
    print("Ctrl+C to stop.")
    print()

    while True:
        all_pass = True
        for label, filename in TESTS:
            print(f"\n>>> {label}")
            if not run_test(filename):
                all_pass = False

        print()
        print("=" * 64)
        print("RUNTIME CYCLE:", "ALL PASS" if all_pass else "ATTENTION / FAIL")
        print("=" * 64)
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
