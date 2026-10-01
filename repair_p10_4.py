from pathlib import Path
import ast
import py_compile
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PATCHER = ROOT / "apply_p10_4.py"

print("=== P10-4 LOCATOR FINAL REPAIR ===")

source = PATCHER.read_text(encoding="utf-8-sig")
tree = ast.parse(source)

target = None

for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if node.name == "find_method_response_guard":
            target = node
            break

if target is None:
    raise RuntimeError("find_method_response_guard NOT FOUND")

lines = source.splitlines(keepends=True)

replacement = '''def find_method_response_guard(source):
    """
    Locate the actual RESPONSE GUARD inside MINH.process().

    The real marker in main.py is:
        # 6. RESPONSE GUARD

    Do not require an exact comment string because the numbered
    section marker intentionally contains a prefix.
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

        if node.name != "process":
            continue

        start = node.lineno
        end = getattr(node, "end_lineno", node.lineno)

        for line_no in range(start, end + 1):
            if line_no <= 0 or line_no > len(source_lines):
                continue

            line = source_lines[line_no - 1]

            if "RESPONSE GUARD" in line:
                print(
                    "RESPONSE GUARD LOCATED:",
                    f"MINH.process() line {line_no}",
                    "|",
                    line.strip(),
                )
                return line_no

    fail(
        "REAL RESPONSE GUARD NOT FOUND INSIDE MINH.process()"
    )
'''

start = target.lineno - 1
end = target.end_lineno

new_source = (
    "".join(lines[:start])
    + replacement
    + "".join(lines[end:])
)

ast.parse(new_source)

tmp = ROOT / "__p10_4_locator_test.py"
tmp.write_text(new_source, encoding="utf-8", newline="\n")

try:
    py_compile.compile(str(tmp), doraise=True)
finally:
    tmp.unlink(missing_ok=True)

PATCHER.write_text(new_source, encoding="utf-8", newline="\n")

print("LOCATOR REPAIR: PASS")
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
    print("P10-4 RESULT: FAIL")
    raise SystemExit(result.returncode)

print()
print("P10-4 RESULT: PASS")
