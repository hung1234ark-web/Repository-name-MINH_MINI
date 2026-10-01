from pathlib import Path

p = Path("main.py")
lines = p.read_text(encoding="utf-8-sig").splitlines()

print("=" * 80)
print("P12-1 REPAIR SOURCE INSPECTION")
print("READ ONLY — NO FILE MODIFICATION")
print("=" * 80)

# Show the exact area around P11 helper
start = 4518
end = min(4570, len(lines))

print("\n" + "=" * 80)
print(f"MAIN.PY LINES {start}-{end}")
print("=" * 80)

for n in range(start, end + 1):
    print(f"{n:5}: {lines[n - 1]}")

print("\n" + "=" * 80)
print("SEARCH P11/P12 ANCHORS")
print("=" * 80)

for i, line in enumerate(lines, 1):
    if (
        "_p11_select_tool" in line
        or "TOOL SELECTOR" in line
        or "P11" in line
    ):
        print(f"{i:5}: {line}")

print("\n" + "=" * 80)
print("P12-1 REPAIR INSPECTION COMPLETE")
print("NO FILES MODIFIED")
print("=" * 80)
