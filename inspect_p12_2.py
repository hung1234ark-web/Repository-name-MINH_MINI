from pathlib import Path

p = Path("main.py")
lines = p.read_text(encoding="utf-8-sig").splitlines()

print("=" * 80)
print("P12-2 EXECUTION ROUTE INSPECTION")
print("READ ONLY — NO FILE MODIFICATION")
print("=" * 80)

ranges = [
    (3750, 3905, "EXECUTION CONTRACT + GATE"),
    (3905, 4045, "DECISION -> EXECUTION"),
    (4045, 4145, "VERIFY + POST EXECUTION"),
    (4325, 4415, "P10/P11/P12 HOOKS"),
]

for start, end, title in ranges:
    print("\n" + "=" * 80)
    print(title)
    print(f"LINES {start}-{end}")
    print("=" * 80)

    for n in range(start, min(end, len(lines)) + 1):
        print(f"{n:5}: {lines[n - 1]}")

print("\n" + "=" * 80)
print("SEARCH TOOL / DECISION / CONTRACT REFERENCES")
print("=" * 80)

for i, line in enumerate(lines, 1):
    if any(
        x in line
        for x in [
            "last_p11_tool_selection",
            "tool_selection",
            "execution_contract",
            "ExecutionContract",
            "decision =",
            "execute_decision(",
        ]
    ):
        print(f"{i:5}: {line}")

print("\n" + "=" * 80)
print("P12-2 INSPECTION COMPLETE")
print("NO FILES MODIFIED")
print("=" * 80)
