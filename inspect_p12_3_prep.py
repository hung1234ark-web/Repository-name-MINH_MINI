from pathlib import Path

files = [
    "observer.py",
    "main.py",
]

print("=" * 100)
print("P12-3 PREP — EXECUTE -> OBSERVE -> VERIFY LIFECYCLE INSPECTION")
print("READ ONLY — NO FILE MODIFICATION")
print("=" * 100)

for filename in files:
    p = Path(filename)

    print("\n" + "=" * 100)
    print("FILE:", filename)
    print("=" * 100)

    if not p.exists():
        print("MISSING")
        continue

    lines = p.read_text(
        encoding="utf-8-sig"
    ).splitlines()

    if filename == "observer.py":
        start = 1
        end = len(lines)

    else:
        # Show execution lifecycle + P12/P4-5/P11/P10 area.
        ranges = [
            (3980, 4165),
            (4680, 4875),
        ]

        for start, end in ranges:
            print(
                f"\n--- main.py lines {start}-{end} ---"
            )

            for i in range(
                start,
                min(end, len(lines)) + 1,
            ):
                print(
                    f"{i:5}: {lines[i - 1]}"
                )

        continue

    for i in range(
        start,
        min(end, len(lines)) + 1,
    ):
        print(
            f"{i:5}: {lines[i - 1]}"
        )

print("\n" + "=" * 100)
print("P12-3 PREP INSPECTION COMPLETE")
print("NO FILES MODIFIED")
print("=" * 100)
