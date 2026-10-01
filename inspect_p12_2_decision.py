from pathlib import Path

p = Path("main.py")
lines = p.read_text(encoding="utf-8-sig").splitlines()

print("=" * 80)
print("P12-2 DECISION -> TOOL -> EXECUTION INSPECTION")
print("READ ONLY — NO FILE MODIFICATION")
print("=" * 80)

ranges = [
    (3625, 3760, "DECISION / ROUTING"),
    (3835, 3895, "CONTRACT GATE"),
    (4035, 4108, "EXECUTE -> OBSERVE -> VERIFY"),
    (4415, 4460, "P10 -> P11 CURRENT HOOK"),
]

for start, end, title in ranges:
    print("\n" + "=" * 80)
    print(title)
    print(f"LINES {start}-{end}")
    print("=" * 80)

    for n in range(start, min(end, len(lines)) + 1):
        print(f"{n:5}: {lines[n - 1]}")

print("\n" + "=" * 80)
print("P12-2 DECISION INSPECTION COMPLETE")
print("NO FILES MODIFIED")
print("=" * 80)
