from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent

FILES = [
    "main.py",
    "execution_contract.py",
    "action.py",
    "app_bridge.py",
    "tool_selector.py",
]

def read(name):
    path = ROOT / name
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8-sig")

def show_methods(source, filename):
    tree = ast.parse(source, filename=filename)

    print(f"\n=== {filename} ===")

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            print(f"CLASS: {node.name}")

            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = []
                    for arg in child.args.args:
                        args.append(arg.arg)

                    print(
                        f"  METHOD: {child.name}"
                        f"({', '.join(args)})"
                        f" [{child.lineno}-{child.end_lineno}]"
                    )

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = []
            for arg in node.args.args:
                args.append(arg.arg)

            print(
                f"FUNCTION: {node.name}"
                f"({', '.join(args)})"
                f" [{node.lineno}-{node.end_lineno}]"
            )

def find_source_context(source, patterns, filename):
    lines = source.splitlines()

    print(f"\n--- {filename} IMPORTANT REFERENCES ---")

    found = set()

    for i, line in enumerate(lines):
        low = line.lower()

        for pattern in patterns:
            if pattern.lower() in low:
                key = (i + 1, pattern)
                if key in found:
                    continue

                found.add(key)

                start = max(0, i - 2)
                end = min(len(lines), i + 4)

                print(f"\n[{i + 1}] MATCH: {pattern}")
                for n in range(start, end):
                    print(f"{n + 1:5}: {lines[n]}")

print("=" * 70)
print("P12-1 ARCHITECTURE DIAGNOSTIC")
print("READ ONLY — NO PROJECT MODIFICATION")
print("=" * 70)

for filename in FILES:
    source = read(filename)

    if source is None:
        print(f"\n{filename}: NOT FOUND")
        continue

    try:
        compile(source, filename, "exec")
        ast.parse(source, filename=filename)
        print(f"\n{filename}: AST + COMPILE PASS")
        show_methods(source, filename)
    except Exception as exc:
        print(f"\n{filename}: AST/COMPILE ERROR: {exc}")

main = read("main.py")

if main:
    find_source_context(
        main,
        [
            "execute_decision",
            "verify_execution_result",
            "execution_contract",
            "execute(",
            "verify(",
            "observe",
            "action",
            "tool_selector",
            "last_p11_tool_selection",
            "last_execution_contract",
        ],
        "main.py",
    )

contract = read("execution_contract.py")

if contract:
    find_source_context(
        contract,
        [
            "class ",
            "def ",
            "ExecutionContract",
            "create_execution_contract",
            "verify",
            "execute",
        ],
        "execution_contract.py",
    )

action = read("action.py")

if action:
    find_source_context(
        action,
        [
            "class ",
            "def ",
            "execute",
            "run",
            "dispatch",
            "action",
        ],
        "action.py",
    )

print("\n" + "=" * 70)
print("P12-1 DIAGNOSTIC COMPLETE")
print("NO FILES MODIFIED")
print("=" * 70)
