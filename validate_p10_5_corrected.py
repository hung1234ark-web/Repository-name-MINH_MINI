from pathlib import Path
import ast
import importlib
import traceback

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"

print("=" * 60)
print("P10-5 RUNTIME VALIDATION — CORRECTED")
print("MinhMiniCore / p10_risk / p10_simulator / p10_judge")
print("=" * 60)

errors = []

def check(name, condition, detail=""):
    if condition:
        print(f"{name}: PASS")
    else:
        print(f"{name}: FAIL")
        if detail:
            print("  " + detail)
        errors.append(name)

# ------------------------------------------------------------
# SOURCE
# ------------------------------------------------------------

src = MAIN.read_text(encoding="utf-8-sig")
tree = ast.parse(src, filename=str(MAIN))
lines = src.splitlines()

check("MAIN FILE", MAIN.exists())
check("MAIN AST", True)

# ------------------------------------------------------------
# MODULE IMPORTS
# ------------------------------------------------------------

for module_name in ("risk", "simulator", "judge"):
    found = False

    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == module_name:
                    found = True

        elif isinstance(node, ast.ImportFrom):
            if node.module == module_name:
                found = True

    check(
        f"P10 MODULE {module_name}",
        found,
        f"import for {module_name} not found"
    )

# ------------------------------------------------------------
# REAL CLASS
# ------------------------------------------------------------

classes = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.ClassDef)
]

core_classes = [
    n for n in classes
    if n.name == "MinhMiniCore"
]

check(
    "MinhMiniCore CLASS",
    bool(core_classes),
    "MinhMiniCore class not found"
)

core = core_classes[0] if core_classes else None

# ------------------------------------------------------------
# __init__
# ------------------------------------------------------------

init = None

if core:
    for n in core.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if n.name == "__init__":
                init = n
                break

check(
    "MinhMiniCore.__init__",
    init is not None,
    "__init__ not found"
)

if init:
    attrs = set()

    for n in ast.walk(init):
        if isinstance(n, ast.Assign):
            targets = n.targets
        elif isinstance(n, ast.AnnAssign):
            targets = [n.target]
        else:
            continue

        for target in targets:
            if (
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id == "self"
            ):
                attrs.add(target.attr)

    for attr in ("p10_risk", "p10_simulator", "p10_judge"):
        check(
            f"INIT self.{attr}",
            attr in attrs,
            f"self.{attr} not found in __init__"
        )

# ------------------------------------------------------------
# P10 EVALUATION METHOD
# ------------------------------------------------------------

eval_method = None

for n in ast.walk(tree):
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if n.name == "_p10_4_run_evaluation":
            eval_method = n
            break

check(
    "P10 EVALUATION METHOD",
    eval_method is not None,
    "_p10_4_run_evaluation not found"
)

# ------------------------------------------------------------
# REAL process() INSIDE MinhMiniCore
# ------------------------------------------------------------

process = None

if core:
    for n in core.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if n.name == "process":
                process = n
                break

check(
    "MinhMiniCore.process",
    process is not None,
    "process method not found inside MinhMiniCore"
)

# ------------------------------------------------------------
# P10 CALL INSIDE REAL process
# ------------------------------------------------------------

p10_call_found = False

if process:
    for n in ast.walk(process):
        if isinstance(n, ast.Call):
            func = n.func

            if isinstance(func, ast.Attribute):
                if func.attr == "_p10_4_run_evaluation":
                    p10_call_found = True

check(
    "P10 CALL INSIDE MinhMiniCore.process",
    p10_call_found,
    "_p10_4_run_evaluation call not found inside real process()"
)

# ------------------------------------------------------------
# RUNTIME IMPORT
# ------------------------------------------------------------

print("\n=== RUNTIME IMPORT ===")

try:
    main_module = importlib.import_module("main")
    check("MAIN IMPORT", True)
except Exception:
    check("MAIN IMPORT", False)
    traceback.print_exc()
    raise SystemExit(1)

# ------------------------------------------------------------
# FIND GLOBAL CORE INSTANCE
# ------------------------------------------------------------

core_instance = None

for name, value in vars(main_module).items():
    if value.__class__.__name__ == "MinhMiniCore":
        core_instance = value
        print(f"CORE INSTANCE FOUND: {name}")
        break

check(
    "GLOBAL MinhMiniCore INSTANCE",
    core_instance is not None,
    "No global MinhMiniCore instance found"
)

if core_instance is None:
    raise SystemExit(1)

# ------------------------------------------------------------
# REAL RUNTIME ATTRIBUTES
# ------------------------------------------------------------

print("\n=== RUNTIME P10 OBJECTS ===")

for attr in ("p10_risk", "p10_simulator", "p10_judge"):
    value = getattr(core_instance, attr, None)

    check(
        f"RUNTIME {attr}",
        value is not None,
        f"{attr} missing or None"
    )

    if value is not None:
        print(
            f"  {attr} TYPE: "
            f"{type(value).__name__}"
        )

# ------------------------------------------------------------
# INITIAL P10 STATE
# ------------------------------------------------------------

print("\n=== INITIAL P10 STATE ===")

initial = getattr(
    core_instance,
    "last_p10_evaluation",
    None
)

print(
    "last_p10_evaluation:",
    "PRESENT" if initial is not None else "NONE"
)

# ------------------------------------------------------------
# SAFE RUNTIME TEST
# ------------------------------------------------------------

print("\n=== SAFE RUNTIME TEST ===")

try:
    result = core_instance.process("xin chao")

    check(
        "PROCESS RUNTIME",
        True
    )

    print(
        "PROCESS RETURN TYPE:",
        type(result).__name__
    )

except Exception:
    check(
        "PROCESS RUNTIME",
        False,
        "exception raised during benign runtime test"
    )
    traceback.print_exc()

# ------------------------------------------------------------
# POST-RUNTIME P10 STATE
# ------------------------------------------------------------

print("\n=== POST-RUNTIME P10 STATE ===")

evaluation = getattr(
    core_instance,
    "last_p10_evaluation",
    None
)

check(
    "P10 EVALUATION STATE",
    isinstance(evaluation, dict),
    "last_p10_evaluation is not a dict"
)

if isinstance(evaluation, dict):

    print(
        "P10 EVALUATION KEYS:",
        sorted(evaluation.keys())
    )

    for key in ("risk", "simulator", "judge"):
        check(
            f"P10 STATE {key}",
            key in evaluation,
            f"{key} missing from last_p10_evaluation"
        )

    if isinstance(evaluation.get("risk"), dict):
        print(
            "RISK RESULT: PRESENT",
            "| verdict =",
            evaluation["risk"].get("verdict"),
            "| risk_level =",
            evaluation["risk"].get("risk_level")
        )
    else:
        print(
            "RISK RESULT:",
            type(evaluation.get("risk")).__name__
        )

    if isinstance(evaluation.get("simulator"), dict):
        print(
            "SIMULATOR RESULT: PRESENT",
            "| status =",
            evaluation["simulator"].get("status")
        )
    else:
        print(
            "SIMULATOR RESULT:",
            type(evaluation.get("simulator")).__name__
        )

    if isinstance(evaluation.get("judge"), dict):
        print(
            "JUDGE RESULT: PRESENT",
            "| verdict =",
            evaluation["judge"].get("verdict"),
            "| decision =",
            evaluation["judge"].get("decision")
        )
    else:
        print(
            "JUDGE RESULT:",
            type(evaluation.get("judge")).__name__
        )

# ------------------------------------------------------------
# STATUS METHOD
# ------------------------------------------------------------

print("\n=== P10 STATUS ===")

status_method = getattr(
    core_instance,
    "_p10_4_get_evaluation_status",
    None
)

check(
    "P10 STATUS METHOD",
    callable(status_method),
    "_p10_4_get_evaluation_status missing"
)

if callable(status_method):
    try:
        status = status_method()

        check(
            "P10 STATUS RUNTIME",
            isinstance(status, dict),
            "status result is not dict"
        )

        print("STATUS:", status)

    except Exception:
        check(
            "P10 STATUS RUNTIME",
            False
        )
        traceback.print_exc()

# ------------------------------------------------------------
# ADVISORY-ONLY STATIC GUARD
# ------------------------------------------------------------

print("\n=== ADVISORY-ONLY GUARDS ===")

dangerous = [
    "self.p10_risk.execute(",
    "self.p10_simulator.execute(",
    "self.p10_judge.execute(",
    "self.p10_risk.run(",
    "self.p10_simulator.run(",
    "self.p10_judge.run(",
]

lower_src = src.lower()

for pattern in dangerous:
    check(
        f"NO {pattern}",
        pattern.lower() not in lower_src,
        f"dangerous direct execution pattern found"
    )

# ------------------------------------------------------------
# EXECUTE -> VERIFY PRESERVATION
# ------------------------------------------------------------

print("\n=== EXECUTION PATH PRESERVATION ===")

check(
    "execute_decision EXISTS",
    "def execute_decision" in src
)

check(
    "verify_execution_result EXISTS",
    "def verify_execution_result" in src
)

# ------------------------------------------------------------
# FINAL
# ------------------------------------------------------------

print("\n" + "=" * 60)

if errors:
    print("P10-5 RESULT: FAIL")
    print("\nFAILURES:")
    for e in errors:
        print(" -", e)
else:
    print("P10-5 RESULT: PASS")
    print("RISK + SIMULATOR + JUDGE RUNTIME VERIFIED")
    print("ADVISORY-ONLY GUARDS VERIFIED")
    print("EXECUTION PATH PRESERVED")

print("=" * 60)
