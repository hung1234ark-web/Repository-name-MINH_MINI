from pathlib import Path

p = Path("main.py")
lines = p.read_text(encoding="utf-8-sig").splitlines()

print("=" * 90)
print("P12-2 _p11_select_tool EXACT SOURCE INSPECTION")
print("READ ONLY — NO FILE MODIFICATION")
print("=" * 90)

start = None
end = None

for i, line in enumerate(lines, 1):
    if line.strip().startswith("def _p11_select_tool("):
        start = i
        break

if start is None:
    print("ERROR: _p11_select_tool NOT FOUND")
    raise SystemExit(1)

for i in range(start + 1, len(lines) + 1):
    stripped = lines[i - 1].strip()

    if (
        stripped.startswith("def ")
        and i > start
    ):
        end = i - 1
        break

if end is None:
    end = min(len(lines), start + 80)

print(f"\nFUNCTION RANGE: {start} - {end}")
print("-" * 90)

for i in range(start, end + 1):
    print(f"{i:5}: {lines[i - 1]}")

print("\n" + "=" * 90)
print("P12-2 CALL-SITE INSPECTION")
print("=" * 90)

for i, line in enumerate(lines, 1):
    if "_p11_select_tool(" in line:
        print(f"\nCALL/DEF AT LINE {i}")
        for n in range(max(1, i - 3), min(len(lines), i + 12) + 1):
            print(f"{n:5}: {lines[n - 1]}")

print("\n" + "=" * 90)
print("INSPECTION COMPLETE")
print("NO FILES MODIFIED")
print("=" * 90)
