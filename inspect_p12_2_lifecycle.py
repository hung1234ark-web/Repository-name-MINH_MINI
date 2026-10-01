from pathlib import Path

p = Path("main.py")
lines = p.read_text(encoding="utf-8-sig").splitlines()

print("=" * 90)
print("P12-2 LIFECYCLE EXACT SOURCE")
print("READ ONLY — NO FILE MODIFICATION")
print("=" * 90)

# Show the actual process execution area.
start = 4015
end = 4145

print(f"\nMAIN.PY LINES {start}-{end}")
print("-" * 90)

for i in range(start, min(end, len(lines)) + 1):
    print(f"{i:5}: {lines[i - 1]}")

print("\n" + "=" * 90)
print("ALL EXECUTION REFERENCES IN PROCESS")
print("=" * 90)

process_start = None
process_end = None

for i, line in enumerate(lines, 1):
    if line.strip().startswith("def process("):
        process_start = i
        break

if process_start is None:
    raise SystemExit("process() NOT FOUND")

for i in range(process_start + 1, len(lines) + 1):
    if lines[i - 1].startswith("    def "):
        process_end = i - 1
        break

if process_end is None:
    process_end = len(lines)

for i in range(process_start, process_end + 1):
    low = lines[i - 1].lower()

    if (
        "execute" in low
        or "execution_result" in low
        or "observe" in low
        or "verify" in low
        or "p12-2" in low
        or "p11" in low
    ):
        print(f"{i:5}: {lines[i - 1]}")

print("\n" + "=" * 90)
print("EXACT SOURCE INSPECTION COMPLETE")
print("NO FILES MODIFIED")
print("=" * 90)
