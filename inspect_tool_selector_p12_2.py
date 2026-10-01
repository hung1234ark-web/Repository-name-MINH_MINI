from pathlib import Path

p = Path("tool_selector.py")
lines = p.read_text(encoding="utf-8-sig").splitlines()

print("=" * 80)
print("P12-2 TOOL SELECTOR MISMATCH INSPECTION")
print("READ ONLY — NO FILE MODIFICATION")
print("=" * 80)

for i, line in enumerate(lines, 1):
    if (
        "def select(" in line
        or "web" in line.lower()
        or "ollama" in line.lower()
        or "decision" in line.lower()
        or "message" in line.lower()
        or "goal" in line.lower()
    ):
        start = max(1, i - 4)
        end = min(len(lines), i + 8)

        print("\n" + "-" * 80)
        print(f"AROUND LINE {i}")
        print("-" * 80)

        for n in range(start, end + 1):
            print(f"{n:5}: {lines[n - 1]}")

print("\n" + "=" * 80)
print("TOOL SELECTOR INSPECTION COMPLETE")
print("NO FILES MODIFIED")
print("=" * 80)
