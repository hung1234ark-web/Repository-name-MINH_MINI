from pathlib import Path
import ast
import shutil
import py_compile
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PATCHER = ROOT / "apply_p10_4.py"
BACKUP = ROOT / "apply_p10_4.py.before_locator_repair"

print("=== P10-4 PATCHER LOCATOR REPAIR ===")

if not PATCHER.exists():
    raise RuntimeError("apply_p10_4.py NOT FOUND")

source = PATCHER.read_text(encoding="utf-8")

if "def find_method_response_guard" not in source:
    raise RuntimeError("find_method_response_guard NOT FOUND")

if not BACKUP.exists():
    shutil.copy2(PATCHER, BACKUP)
    print("PATCHER BACKUP: PASS")
else:
    print("PATCHER BACKUP: EXISTS")

tree = ast.parse(source)

target = None

for node in ast.walk(tree):
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        continue

    if node.name != "find_method_response_guard":
        continue

    target = node
    break

if target is None:
    raise RuntimeError("AST TARGET FUNCTION NOT FOUND")

lines = source.splitlines(keepends=True)

start = target.lineno - 1
end = target.end_lineno

replacement = '''def find_method_response_guard(source):
    """
    Locate the real RESPONSE GUARD inside MINH.process().

    main.py contains multiple RESPONSE GUARD markers:
    - module-level documentation/comment
    - guard_answer() helper
    - the actual execution-flow guard inside MINH.process()

    P10-4 must be inserted into MINH.process(), immediately before
    its real response guard. This function deliberately selects the
    deepest/latest matching guard contained by a self method.
    """
    tree = ast.parse(source)
    source_lines = source.splitlines()

    candidates = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        args = node.args.args
        if not args or args[0].arg != "self":
            continue

        if not hasattr(node, "lineno") or not hasattr(node, "end_lineno"):
            continue

        for line_no in range(node.lineno, node.end_lineno + 1):
            if line_no <= 0 or line_no > len(source_lines):
                continue

            text = source_lines[line_no - 1]

            if "# RESPONSE GUARD" in text:
                candidates.append(
                    (
                        node.name == "process",
                        line_no,
                        node.name,
                        node.lineno,
                        node.end_lineno,
                    )
                )

    if not candidates:
        fail(
            "NO RESPONSE GUARD FOUND INSIDE self METHOD"
        )

    process_candidates = [
        item for item in candidates
        if item[2] == "process"
    ]

    if process_candidates:
        candidates = process_candidates

    candidates.sort(
        key=lambda item: (
            item[0],
            item[1],
            item[4],
        ),
        reverse=True,
    )

    selected = candidates[0]

    response_line = selected[1]

    print(
        "RESPONSE GUARD LOCATED:",
        f"{selected[2]}()",
        f"line {response_line}",
    )

    return response_line
'''

new_source = "".join(lines[:start]) + replacement + "".join(lines[end:])

# Validate the repaired patcher before writing it.
ast.parse(new_source)

temp = PATCHER.with_name("apply_p10_4.repaired.tmp.py")
temp.write_text(new_source, encoding="utf-8")

try:
    py_compile.compile(
        str(temp),
        doraise=True,
    )
except Exception:
    temp.unlink(missing_ok=True)
    raise

shutil.move(str(temp), str(PATCHER))

print("PATCHER WRITE: PASS")
print("PATCHER COMPILE: PASS")
print()
print("=== RUNNING P10-4 ===")
print()

result = subprocess.run(
    [sys.executable, str(PATCHER)],
    cwd=str(ROOT),
)

if result.returncode != 0:
    print()
    print("P10-4 PATCHER RESULT: FAIL")
    print("PATCHER LOCATOR WAS REPAIRED, BUT INTEGRATION FAILED.")
    print("main.py should have been protected by the patcher's rollback.")
    raise SystemExit(result.returncode)

print()
print("P10-4 PATCHER RESULT: PASS")
