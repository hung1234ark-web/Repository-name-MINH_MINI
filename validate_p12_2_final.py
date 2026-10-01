from pathlib import Path
import ast
import py_compile

p = Path("main.py")
source = p.read_text(encoding="utf-8-sig")
lines = source.splitlines()

print("=" * 90)
print("P12-2 FINAL STRUCTURAL VALIDATION")
print("READ ONLY — NO EXECUTION")
print("=" * 90)

ast.parse(source)
py_compile.compile(str(p), doraise=True)

print("MAIN AST: PASS")
print("MAIN COMPILE: PASS")

# Locate important lifecycle anchors.
anchors = {
    "P12-2 PREPARE": "_p12_2_prepare_tool_selection",
    "EXECUTE": "answer, execution_result = self.execute_decision(",
    "P12-1 OBSERVE": "# P12-1 EXECUTE -> OBSERVE",
    "P4-5 VERIFY": "# P45_EXECUTION_VERIFY",
    "P10 EVALUATION": "# P10-4 EVALUATION",
    "P11 SELECTOR": "_p11_select_tool(",
}

positions = {}

for name, needle in anchors.items():
    hits = [
        i + 1
        for i, line in enumerate(lines)
        if needle in line
    ]
    positions[name] = hits

    print(f"{name}: {hits}")

# The P12-2 helper itself may contain the selector call.
# We care about the actual lifecycle ordering in process().
def find_line(needle, start=0):
    for i in range(start, len(lines)):
        if needle in lines[i]:
            return i + 1
    return None

process_line = find_line("def process(")

if process_line is None:
    raise SystemExit("PROCESS METHOD NOT FOUND")

print("PROCESS METHOD:", process_line)

p12_prepare = find_line(
    "# P12-2 JUDGE -> TOOL SELECTOR -> EXECUTE",
    process_line - 1,
)

execute_line = find_line(
    "answer, execution_result = self.execute_decision(",
    process_line - 1,
)

observe_line = find_line(
    "# P12-1 EXECUTE -> OBSERVE",
    process_line - 1,
)

verify_line = find_line(
    "# P45_EXECUTION_VERIFY",
    process_line - 1,
)

print("\n=== LIFECYCLE ORDER ===")
print("P12-2 PREPARE:", p12_prepare)
print("EXECUTE:", execute_line)
print("OBSERVE:", observe_line)
print("VERIFY:", verify_line)

if not all(
    x is not None
    for x in (
        p12_prepare,
        execute_line,
        observe_line,
        verify_line,
    )
):
    raise SystemExit(
        "REQUIRED LIFECYCLE ANCHOR MISSING"
    )

if not (
    p12_prepare
    < execute_line
    < observe_line
    < verify_line
):
    raise SystemExit(
        "LIFECYCLE ORDER FAILED"
    )

print("LIFECYCLE ORDER: PASS")

# Check the selector call in the P12-2 helper.
helper_line = find_line(
    "def _p12_2_prepare_tool_selection("
)

if helper_line is None:
    raise SystemExit(
        "P12-2 HELPER NOT FOUND"
    )

helper_end = len(lines)

for i in range(helper_line, len(lines)):
    stripped = lines[i].strip()
    if (
        i > helper_line
        and stripped.startswith("def ")
    ):
        helper_end = i
        break

helper_text = "\n".join(
    lines[helper_line - 1:helper_end]
)

if "goal=message" not in helper_text:
    raise SystemExit(
        "P12-2 helper does not pass message to selector"
    )

print("MESSAGE -> SELECTOR: PASS")

# Ensure selector remains advisory.
if '"advisory_only"] = True' not in helper_text:
    print(
        "WARNING: advisory_only assignment not found "
        "in helper text"
    )
else:
    print("ADVISORY FLAG: PASS")

# Count execute_decision occurrences inside process.
process_end = len(lines)

for i in range(process_line, len(lines)):
    if (
        i > process_line
        and lines[i].startswith("    def ")
    ):
        process_end = i
        break

process_text = "\n".join(
    lines[process_line - 1:process_end]
)

execute_calls = process_text.count(
    "self.execute_decision("
)

print(
    "EXECUTE_DECISION CALLS IN PROCESS:",
    execute_calls,
)

if execute_calls != 1:
    raise SystemExit(
        "EXECUTE PATH IS NOT SINGLE"
    )

print("SINGLE EXECUTION PATH: PASS")

print("\n" + "=" * 90)
print("P12-2 FINAL STRUCTURAL VALIDATION: PASS")
print("NO FILES MODIFIED")
print("=" * 90)
