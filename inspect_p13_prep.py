from pathlib import Path
import ast
import py_compile

ROOT = Path.cwd()

FILES = [
    "main.py",
    "diagnose_action_handler.py",
    "action.py",
    "execution_contract.py",
    "task_planner.py",
    "state_manager.py",
]

RANGES = {
    "main.py": [
        (4120, 4250),
        (4650, 4890),
    ],
    "diagnose_action_handler.py": [
        (1, 500),
    ],
    "action.py": [
        (1, 260),
    ],
    "execution_contract.py": [
        (1, 350),
    ],
    "task_planner.py": [
        (1, 400),
    ],
    "state_manager.py": [
        (1, 400),
    ],
}

print("=" * 100)
print("P13 PREP — DIAGNOSIS -> RECOVERY -> REPLAN")
print("READ ONLY — NO FILE MODIFICATION")
print("=" * 100)

for filename in FILES:
    path = ROOT / filename

    print("\n" + "=" * 100)
    print("FILE:", filename)
    print("=" * 100)

    if not path.exists():
        print("STATUS: MISSING")
        continue

    source = path.read_text(
        encoding="utf-8-sig"
    )

    print("SIZE:", len(source), "bytes")

    try:
        tree = ast.parse(source)
        print("AST: PASS")
    except Exception as exc:
        print("AST: FAIL:", repr(exc))
        continue

    try:
        py_compile.compile(
            str(path),
            doraise=True,
        )
        print("COMPILE: PASS")
    except Exception as exc:
        print("COMPILE: FAIL:", repr(exc))

    print("\n--- DEFINITIONS ---")

    for node in tree.body:
        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
            ),
        ):
            print(
                f"{node.__class__.__name__}: "
                f"{node.name} "
                f"(line {node.lineno})"
            )

    for start, end in RANGES.get(
        filename,
        [],
    ):
        lines = source.splitlines()

        if start > len(lines):
            continue

        end = min(
            end,
            len(lines),
        )

        print(
            f"\n--- SOURCE {start}-{end} ---"
        )

        for number in range(
            start,
            end + 1,
        ):
            print(
                f"{number:5}: "
                f"{lines[number - 1]}"
            )

print("\n" + "=" * 100)
print("P13 PREP INSPECTION COMPLETE")
print("NO FILES MODIFIED")
print("=" * 100)
