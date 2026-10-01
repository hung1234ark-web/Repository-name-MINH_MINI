from pathlib import Path
import ast
import importlib
import inspect
import traceback

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"

print("============================================================")
print("P10-5 RUNTIME VALIDATION")
print("RISK + SIMULATOR + JUDGE")
print("============================================================")

errors = []
warnings = []

def check(name, condition, detail=""):
    if condition:
        print(f"{name}: PASS")
    else:
        print(f"{name}: FAIL")
        if detail:
            print("  ", detail)
        errors.append(name)

# ------------------------------------------------------------
# 1. CORE FILE
# ------------------------------------------------------------

check(
    "MAIN FILE",
    MAIN.exists(),
    "main.py not found"
)

if errors:
    raise SystemExit(1)

source = MAIN.read_text(encoding="utf-8-sig")

# ------------------------------------------------------------
# 2. AST STRUCTURE
# ------------------------------------------------------------

try:
    tree = ast.parse(source)
    print("MAIN AST: PASS")
except Exception as exc:
    print("MAIN AST: FAIL")
    print(exc)
    raise SystemExit(1)

# ------------------------------------------------------------
# 3. P10 IMPORTS
# ------------------------------------------------------------

required_modules = [
    "risk",
    "simulator",
    "judge",
]

for module in required_modules:
    check(
        f"P10 MODULE {module}",
        module in source,
        f"{module} reference not found in main.py"
    )

# ------------------------------------------------------------
# 4. P10 INSTANCE ATTRIBUTES
# ------------------------------------------------------------

required_attrs = [
    "risk",
    "simulator",
    "judge",
]

for attr in required_attrs:
    check(
        f"P10 ATTR {attr}",
        f"self.{attr}" in source,
        f"self.{attr} not found"
    )

# ------------------------------------------------------------
# 5. P10 EVALUATION HOOK
# ------------------------------------------------------------

evaluation_names = [
    "_p10_4_run_evaluation",
    "_p10_4_evaluate",
    "_p10_run_evaluation",
]

evaluation_found = [
    name for name in evaluation_names
    if name in source
]

check(
    "P10 EVALUATION HOOK",
    bool(evaluation_found),
    "No known P10 evaluation hook found"
)

# ------------------------------------------------------------
# 6. ACTUAL MINH.process()
# ------------------------------------------------------------

process_nodes = []

for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if node.name == "process":
            args = node.args.args
            if args and args[0].arg == "self":
                process_nodes.append(node)

check(
    "MINH.process METHOD",
    bool(process_nodes),
    "MINH.process() not found"
)

process_node = process_nodes[-1] if process_nodes else None

if process_node:
    print(
        "PROCESS RANGE:",
        process_node.lineno,
        "-",
        process_node.end_lineno
    )

# ------------------------------------------------------------
# 7. P10 CALL MUST BE INSIDE MINH.process()
# ------------------------------------------------------------

if process_node:

    process_source = "\n".join(
        source.splitlines()[
            process_node.lineno - 1 :
            process_node.end_lineno
        ]
    )

    p10_call_present = any(
        name in process_source
        for name in evaluation_names
    )

    check(
        "P10 CALL INSIDE PROCESS",
        p10_call_present,
        "P10 evaluation call is not inside MINH.process()"
    )

# ------------------------------------------------------------
# 8. IMPORT MAIN
# ------------------------------------------------------------

print()
print("=== RUNTIME IMPORT ===")

try:
    import main

    print("MAIN IMPORT: PASS")
except Exception:
    print("MAIN IMPORT: FAIL")
    traceback.print_exc()
    raise SystemExit(1)

# ------------------------------------------------------------
# 9. GLOBAL MINH
# ------------------------------------------------------------

instance = getattr(main, "MINH", None)

check(
    "GLOBAL MINH",
    instance is not None,
    "main.MINH is missing"
)

if instance is None:
    raise SystemExit(1)

# ------------------------------------------------------------
# 10. P10 RUNTIME OBJECTS
# ------------------------------------------------------------

for attr in required_attrs:
    value = getattr(instance, attr, None)

    check(
        f"RUNTIME {attr}",
        value is not None,
        f"MINH.{attr} is missing"
    )

    if value is not None:
        print(
            f"  {attr} type:",
            type(value).__name__
        )

# ------------------------------------------------------------
# 11. P10 STATUS
# ------------------------------------------------------------

print()
print("=== P10 STATUS ===")

status_values = {}

for attr in [
    "last_p10_evaluation",
    "last_p10_risk",
    "last_p10_simulation",
    "last_p10_judgement",
    "last_p10_judge",
]:
    if hasattr(instance, attr):
        status_values[attr] = getattr(instance, attr)
        print(f"{attr}: PRESENT")
    else:
        print(f"{attr}: NOT PRESENT")

# ------------------------------------------------------------
# 12. SAFE RUNTIME SMOKE
# ------------------------------------------------------------

print()
print("=== SAFE RUNTIME SMOKE ===")

answer = None

try:
    # Benign conversational input.
    # This must not request Web, Action, Code, or external execution.
    answer = instance.process("xin chao")

    print("PROCESS CALL: PASS")
    print("ANSWER TYPE:", type(answer).__name__)

except Exception:
    print("PROCESS CALL: FAIL")
    traceback.print_exc()
    errors.append("PROCESS CALL")

# ------------------------------------------------------------
# 13. VERIFY P10 STATE AFTER RUNTIME
# ------------------------------------------------------------

print()
print("=== POST-RUNTIME P10 STATE ===")

for attr in [
    "last_p10_evaluation",
    "last_p10_risk",
    "last_p10_simulation",
    "last_p10_judgement",
    "last_p10_judge",
]:

    if hasattr(instance, attr):
        value = getattr(instance, attr)

        print(
            attr,
            "=>",
            type(value).__name__,
            "|",
            "NONE" if value is None else "SET"
        )

# ------------------------------------------------------------
# 14. ADVISORY-ONLY GUARD
# ------------------------------------------------------------

print()
print("=== ADVISORY-ONLY GUARD ===")

dangerous_patterns = [
    "self.risk.execute(",
    "self.simulator.execute(",
    "self.judge.execute(",
    "self.risk.run_action(",
    "self.simulator.run_action(",
    "self.judge.run_action(",
]

for pattern in dangerous_patterns:
    check(
        f"NO EXECUTION {pattern}",
        pattern not in source,
        f"Forbidden execution pattern found: {pattern}"
    )

# ------------------------------------------------------------
# 15. EXECUTION PATH PRESERVATION
# ------------------------------------------------------------

print()
print("=== EXECUTION PATH ===")

required_execution_markers = [
    "execute_decision",
    "verify_execution_result",
]

for marker in required_execution_markers:
    check(
        f"EXECUTION MARKER {marker}",
        marker in source,
        f"{marker} missing"
    )

# ------------------------------------------------------------
# 16. FINAL RESULT
# ------------------------------------------------------------

print()
print("============================================================")

if errors:
    print("P10-5 RUNTIME VALIDATION: FAIL")
    print()
    print("FAILED CHECKS:")
    for item in errors:
        print(" -", item)
    print("============================================================")
    raise SystemExit(1)

print("P10-5 RUNTIME VALIDATION: PASS")
print("RISK: PRESENT")
print("SIMULATOR: PRESENT")
print("JUDGE: PRESENT")
print("MAIN: RUNTIME OK")
print("EXECUTION PATH: PRESERVED")
print("P10 MODE: ADVISORY ONLY")
print("============================================================")
