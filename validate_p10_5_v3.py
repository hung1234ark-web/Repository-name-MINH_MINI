from pathlib import Path
import ast
import importlib
import traceback

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"

print("=" * 60)
print("P10-5 RUNTIME VALIDATION V3")
print("DIRECT P10 TEST — NO PROCESS / NO OLLAMA")
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

check("MAIN FILE", MAIN.exists())
check("MAIN AST", True)

# ------------------------------------------------------------
# IMPORTS — accept imports inside try blocks
# ------------------------------------------------------------

imports = set()

for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        for alias in node.names:
            imports.add(alias.name)

    elif isinstance(node, ast.ImportFrom):
        if node.module:
            imports.add(node.module)

for module_name in ("risk", "simulator", "judge"):
    check(
        f"P10 MODULE {module_name}",
        module_name in imports,
        f"{module_name} not detected in AST imports"
    )

# ------------------------------------------------------------
# REAL CLASS
# ------------------------------------------------------------

core_classes = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.ClassDef)
    and n.name == "MinhMiniCore"
]

check(
    "MinhMiniCore CLASS",
    bool(core_classes)
)

core = core_classes[0] if core_classes else None

# ------------------------------------------------------------
# INIT ATTRIBUTES
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
    init is not None
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

    for attr in (
        "p10_risk",
        "p10_simulator",
        "p10_judge",
        "last_p10_evaluation",
    ):
        check(
            f"INIT self.{attr}",
            attr in attrs
        )

# ------------------------------------------------------------
# P10 METHOD
# ------------------------------------------------------------

evaluation_method = None

for n in ast.walk(tree):
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if n.name == "_p10_4_run_evaluation":
            evaluation_method = n
            break

check(
    "P10 EVALUATION METHOD",
    evaluation_method is not None
)

# ------------------------------------------------------------
# PROCESS
# ------------------------------------------------------------

real_process = None

if core:
    for n in core.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if n.name == "process":
                real_process = n
                break

check(
    "MinhMiniCore.process",
    real_process is not None
)

if real_process:
    call_found = False

    for n in ast.walk(real_process):
        if isinstance(n, ast.Call):
            if isinstance(n.func, ast.Attribute):
                if n.func.attr == "_p10_4_run_evaluation":
                    call_found = True

    check(
        "P10 CALL INSIDE PROCESS",
        call_found
    )

# ------------------------------------------------------------
# EXECUTION PATH
# ------------------------------------------------------------

check(
    "execute_decision EXISTS",
    "def execute_decision" in src
)

check(
    "verify_execution_result EXISTS",
    "def verify_execution_result" in src
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
# GLOBAL MINH
# ------------------------------------------------------------

instance = getattr(main_module, "MINH", None)

check(
    "GLOBAL MINH",
    instance is not None
)

if instance is None:
    raise SystemExit(1)

print(
    "MINH TYPE:",
    type(instance).__name__
)

check(
    "MINH TYPE MinhMiniCore",
    type(instance).__name__ == "MinhMiniCore"
)

# ------------------------------------------------------------
# RUNTIME OBJECTS
# ------------------------------------------------------------

print("\n=== P10 RUNTIME OBJECTS ===")

risk = getattr(instance, "p10_risk", None)
simulator = getattr(instance, "p10_simulator", None)
judge = getattr(instance, "p10_judge", None)

check(
    "RUNTIME p10_risk",
    risk is not None
)

check(
    "RUNTIME p10_simulator",
    simulator is not None
)

check(
    "RUNTIME p10_judge",
    judge is not None
)

if risk:
    print("  RISK TYPE:", type(risk).__name__)

if simulator:
    print("  SIMULATOR TYPE:", type(simulator).__name__)

if judge:
    print("  JUDGE TYPE:", type(judge).__name__)

# ------------------------------------------------------------
# DIRECT P10 EVALUATION
# NO PROCESS
# NO OLLAMA
# ------------------------------------------------------------

print("\n=== DIRECT P10 EVALUATION ===")

evaluation = None

try:

    evaluation = instance._p10_4_run_evaluation(
        goal={
            "goal": "runtime validation",
            "intent": "test",
        },
        plan={
            "steps": [
                {
                    "action": "observe",
                    "description": "safe validation"
                }
            ]
        },
        result={
            "status": "verified",
            "success": True,
        },
    )

    check(
        "P10 DIRECT EVALUATION",
        isinstance(evaluation, dict),
        "evaluation did not return dict"
    )

except Exception:
    check(
        "P10 DIRECT EVALUATION",
        False,
        "exception raised during direct P10 evaluation"
    )
    traceback.print_exc()

# ------------------------------------------------------------
# RESULT STRUCTURE
# ------------------------------------------------------------

if isinstance(evaluation, dict):

    print("\n=== P10 RESULT STRUCTURE ===")

    print(
        "TOP-LEVEL KEYS:",
        sorted(evaluation.keys())
    )

    for key in ("risk", "simulator", "judge"):
        value = evaluation.get(key)

        check(
            f"P10 RESULT {key}",
            value is not None,
            f"{key} missing from evaluation"
        )

        if isinstance(value, dict):
            print(
                f"{key.upper()} TYPE: dict"
            )
            print(
                f"{key.upper()} KEYS:",
                sorted(value.keys())
            )
        else:
            print(
                f"{key.upper()} TYPE:",
                type(value).__name__
            )

# ------------------------------------------------------------
# SAVED STATE
# ------------------------------------------------------------

saved = getattr(
    instance,
    "last_p10_evaluation",
    None
)

check(
    "LAST P10 EVALUATION",
    isinstance(saved, dict),
    "last_p10_evaluation is not dict after evaluation"
)

if isinstance(saved, dict):
    print(
        "SAVED P10 KEYS:",
        sorted(saved.keys())
    )

# ------------------------------------------------------------
# STATUS
# ------------------------------------------------------------

print("\n=== P10 STATUS ===")

status_method = getattr(
    instance,
    "_p10_4_get_evaluation_status",
    None
)

check(
    "P10 STATUS METHOD",
    callable(status_method)
)

if callable(status_method):

    try:
        status = status_method()

        check(
            "P10 STATUS RUNTIME",
            isinstance(status, dict)
        )

        print("STATUS:", status)

    except Exception:
        check(
            "P10 STATUS RUNTIME",
            False
        )
        traceback.print_exc()

# ------------------------------------------------------------
# ADVISORY GUARD
# ------------------------------------------------------------

print("\n=== ADVISORY-ONLY GUARD ===")

dangerous_patterns = (
    "self.p10_risk.execute(",
    "self.p10_simulator.execute(",
    "self.p10_judge.execute(",
    "self.p10_risk.run(",
    "self.p10_simulator.run(",
    "self.p10_judge.run(",
)

lower_src = src.lower()

for pattern in dangerous_patterns:
    check(
        "NO " + pattern,
        pattern.lower() not in lower_src
    )

# ------------------------------------------------------------
# FINAL
# ------------------------------------------------------------

print("\n" + "=" * 60)

if errors:
    print("P10-5 RESULT: FAIL")
    print("\nFAILURES:")
    for error in errors:
        print(" -", error)
else:
    print("P10-5 RESULT: PASS")
    print("DIRECT RISK TEST: PASS")
    print("DIRECT SIMULATOR TEST: PASS")
    print("DIRECT JUDGE TEST: PASS")
    print("P10 STATE: PASS")
    print("ADVISORY-ONLY: PASS")
    print("EXECUTION PATH: PRESERVED")

print("=" * 60)
