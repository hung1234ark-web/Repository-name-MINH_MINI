from pathlib import Path
import ast
import py_compile
import shutil
import sys


ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"

RISK = ROOT / "risk.py"
SIMULATOR = ROOT / "simulator.py"
JUDGE = ROOT / "judge.py"

BACKUP = ROOT / "main.py.before_p10_4_integration"
TEMP = ROOT / "__p10_4_temp_main.py"

MARKER = "P10-4 RISK + SIMULATOR + JUDGE"


print("=== P10-4 RISK + SIMULATOR + JUDGE INTEGRATION ===")


def fail(message: str):
    raise RuntimeError(message)


def compile_file(path: Path):
    py_compile.compile(
        str(path),
        doraise=True,
    )


def compile_source(
    source: str,
    filename: str,
):
    compile(
        source,
        filename,
        "exec",
    )


def parse_ast(
    source: str,
    label: str,
):
    try:
        return ast.parse(source)
    except SyntaxError as exc:
        fail(
            f"{label}: AST PARSE FAILED: {exc}"
        )


def line_offset(
    source: str,
    line_number: int,
):
    lines = source.splitlines(
        keepends=True
    )

    if line_number < 1:
        fail("INVALID LINE NUMBER")

    if line_number > len(lines):
        fail("LINE NUMBER OUT OF RANGE")

    return sum(
        len(line)
        for line in lines[:line_number - 1]
    )


def replace_once(
    source: str,
    old: str,
    new: str,
    label: str,
):
    count = source.count(old)

    if count != 1:
        fail(
            f"{label}: EXPECTED 1 MATCH, FOUND {count}"
        )

    return source.replace(
        old,
        new,
        1,
    )


def get_line_indent(
    source: str,
    line_number: int,
):
    lines = source.splitlines(
        keepends=True
    )

    line = lines[line_number - 1]

    return line[
        :len(line) - len(line.lstrip(" \t"))
    ]


def find_import_insertion_point(
    source: str,
):
    tree = parse_ast(
        source,
        "MAIN.PY",
    )

    last_import = None

    for node in tree.body:
        if isinstance(
            node,
            (
                ast.Import,
                ast.ImportFrom,
            ),
        ):
            last_import = node

    if last_import is None:
        fail(
            "NO MODULE IMPORT BLOCK FOUND"
        )

    end_lineno = getattr(
        last_import,
        "end_lineno",
        None,
    )

    if end_lineno is None:
        fail(
            "IMPORT END LINE UNAVAILABLE"
        )

    return line_offset(
        source,
        end_lineno + 1,
    )


def find_method_response_guard(source):
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


def assert_future_import_order(
    source: str,
):
    marker_pos = source.find(
        MARKER
    )

    if marker_pos < 0:
        fail(
            "P10 MARKER NOT FOUND"
        )

    tree = parse_ast(
        source,
        "FUTURE GUARD",
    )

    for node in tree.body:
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "__future__"
        ):
            position = line_offset(
                source,
                node.lineno,
            )

            if position > marker_pos:
                fail(
                    "FUTURE IMPORT AFTER P10 BLOCK"
                )

    print(
        "FUTURE IMPORT ORDER: PASS"
    )


# =========================================================
# FILE CHECK
# =========================================================

for path, name in [
    (MAIN, "MAIN.PY"),
    (RISK, "RISK.PY"),
    (SIMULATOR, "SIMULATOR.PY"),
    (JUDGE, "JUDGE.PY"),
]:
    if not path.exists():
        fail(
            f"{name}: MISSING"
        )

print(
    "CORE FILES: PASS"
)


# =========================================================
# PRECOMPILE
# =========================================================

for path in [
    RISK,
    SIMULATOR,
    JUDGE,
    MAIN,
]:
    compile_file(path)

print(
    "PRECOMPILE: PASS"
)


# =========================================================
# READ
# =========================================================

original = MAIN.read_text(
    encoding="utf-8"
)


# =========================================================
# DUPLICATE
# =========================================================

if MARKER in original:
    fail(
        "P10-4 ALREADY INTEGRATED"
    )

print(
    "DUPLICATE GUARD: PASS"
)


# =========================================================
# ANCHORS
# =========================================================

required = [
    "_p9_6_run_evaluation",
    "# RESPONSE GUARD",
    "# STATUS",
    "self.last_p9_evaluation",
]

for marker in required:
    if marker not in original:
        fail(
            "MAIN.PY ANCHOR MISSING: "
            + marker
        )

print(
    "MAIN ANCHORS: PASS"
)


# =========================================================
# IMPORTS
# =========================================================

import_pos = find_import_insertion_point(
    original
)

p10_imports = (
    "\n"
    "# ============================================================\n"
    "# P10-4 RISK + SIMULATOR + JUDGE\n"
    "# ============================================================\n"
    "try:\n"
    "    from risk import create_risk\n"
    "    from simulator import create_simulator\n"
    "    from judge import create_judge\n"
    "except Exception as _p10_4_import_error:\n"
    "    create_risk = None\n"
    "    create_simulator = None\n"
    "    create_judge = None\n"
    "    _p10_4_import_error = str(_p10_4_import_error)\n"
    "\n"
)

patched = (
    original[:import_pos]
    + p10_imports
    + original[import_pos:]
)

print(
    "P10 IMPORTS: PASS"
)

assert_future_import_order(
    patched
)


# =========================================================
# INIT
# =========================================================

init_anchor = "self.last_p9_evaluation"

init_pos = patched.find(
    init_anchor
)

init_start = patched.rfind(
    "\n",
    0,
    init_pos,
) + 1

init_end = patched.find(
    "\n",
    init_pos,
)

if init_end < 0:
    init_end = len(patched)
else:
    init_end += 1

init_indent = get_line_indent(
    patched,
    patched[:init_start].count("\n") + 1,
)

init_block = (
    init_indent
    + "# P10-4 INIT\n"
    + init_indent
    + "self.p10_risk = (\n"
    + init_indent
    + "    create_risk()\n"
    + init_indent
    + "    if create_risk is not None\n"
    + init_indent
    + "    else None\n"
    + init_indent
    + ")\n"
    + init_indent
    + "self.p10_simulator = (\n"
    + init_indent
    + "    create_simulator()\n"
    + init_indent
    + "    if create_simulator is not None\n"
    + init_indent
    + "    else None\n"
    + init_indent
    + ")\n"
    + init_indent
    + "self.p10_judge = (\n"
    + init_indent
    + "    create_judge()\n"
    + init_indent
    + "    if create_judge is not None\n"
    + init_indent
    + "    else None\n"
    + init_indent
    + ")\n"
    + init_indent
    + "self.last_p10_evaluation = None\n"
)

patched = (
    patched[:init_end]
    + init_block
    + patched[init_end:]
)

print(
    "P10 INSTANCES: PASS"
)


# =========================================================
# HELPERS
# =========================================================

status_marker = "\n    # STATUS"

if status_marker not in patched:
    status_marker = "\n    def status"

if status_marker not in patched:
    fail(
        "STATUS ANCHOR NOT FOUND"
    )

helper_block = """
    # =========================================================
    # P10-4 RISK + SIMULATOR + JUDGE
    # =========================================================

    def _p10_4_run_evaluation(
        self,
        goal=None,
        plan=None,
        result=None,
    ):
        try:
            risk_result = (
                self.p10_risk.evaluate(
                    goal=goal,
                    plan=plan,
                    result=result,
                )
                if self.p10_risk is not None
                else None
            )

            simulator_result = (
                self.p10_simulator.simulate(
                    goal=goal,
                    plan=plan,
                    result=result,
                )
                if self.p10_simulator is not None
                else None
            )

            p9_data = (
                self.last_p9_evaluation
                if isinstance(
                    self.last_p9_evaluation,
                    dict,
                )
                else {}
            )

            judge_result = (
                self.p10_judge.evaluate(
                    critic=p9_data.get("critic"),
                    red_team=p9_data.get("red_team"),
                    fact_check=p9_data.get("fact_check"),
                    combined=p9_data.get("combined"),
                    risk=risk_result,
                    simulator=simulator_result,
                )
                if self.p10_judge is not None
                else None
            )

            self.last_p10_evaluation = {
                "risk": risk_result,
                "simulator": simulator_result,
                "judge": judge_result,
            }

            return self.last_p10_evaluation

        except Exception as exc:
            self.last_p10_evaluation = {
                "risk": None,
                "simulator": None,
                "judge": {
                    "verdict": "review",
                    "decision": "review",
                    "status": "review",
                    "valid": False,
                    "score": 0.0,
                    "issues": [
                        "p10_evaluation_exception"
                    ],
                    "warnings": [],
                    "reason": str(exc),
                    "version": "P10-4.0",
                },
            }

            return self.last_p10_evaluation

    def _p10_4_get_evaluation_status(self):
        data = self.last_p10_evaluation

        if not isinstance(data, dict):
            return {
                "available": False,
                "verdict": None,
                "decision": None,
                "status": None,
                "score": None,
            }

        judge = data.get("judge")

        if not isinstance(judge, dict):
            return {
                "available": False,
                "verdict": None,
                "decision": None,
                "status": None,
                "score": None,
            }

        return {
            "available": True,
            "verdict": judge.get("verdict"),
            "decision": judge.get("decision"),
            "status": judge.get("status"),
            "score": judge.get("score"),
        }

"""

patched = replace_once(
    patched,
    status_marker,
    "\n" + helper_block + status_marker,
    "P10 HELPERS",
)

print(
    "P10 HELPERS: PASS"
)


# =========================================================
# RESPONSE GUARD TARGET
# =========================================================

response_line = find_method_response_guard(
    patched
)

response_lines = patched.splitlines(
    keepends=True
)

response_pos = sum(
    len(line)
    for line in response_lines[:response_line - 1]
)

response_indent = get_line_indent(
    patched,
    response_line,
)

evaluation_block = (
    response_indent
    + "# P10-4 EVALUATION — ADVISORY ONLY\n"
    + response_indent
    + "try:\n"
    + response_indent
    + "    _p10_goal = None\n"
    + response_indent
    + "    _p10_plan = None\n"
    + response_indent
    + "    _p10_result = {}\n"
    + "\n"
    + response_indent
    + "    if hasattr(self, 'goal_manager'):\n"
    + response_indent
    + "        try:\n"
    + response_indent
    + "            _p10_goal = self.goal_manager.get_goal()\n"
    + response_indent
    + "        except Exception:\n"
    + response_indent
    + "            _p10_goal = None\n"
    + "\n"
    + response_indent
    + "    if hasattr(self, 'task_planner'):\n"
    + response_indent
    + "        try:\n"
    + response_indent
    + "            _p10_plan = self.task_planner.get_plan()\n"
    + response_indent
    + "        except Exception:\n"
    + response_indent
    + "            _p10_plan = None\n"
    + "\n"
    + response_indent
    + "    _p10_last_result = getattr(\n"
    + response_indent
    + "        self,\n"
    + response_indent
    + "        'last_execution_result',\n"
    + response_indent
    + "        {},\n"
    + response_indent
    + "    )\n"
    + "\n"
    + response_indent
    + "    if isinstance(_p10_last_result, dict):\n"
    + response_indent
    + "        _p10_result = dict(_p10_last_result)\n"
    + "\n"
    + response_indent
    + "    if hasattr(self, 'last_execution_verification'):\n"
    + response_indent
    + "        _p10_result['verification'] = getattr(\n"
    + response_indent
    + "            self,\n"
    + response_indent
    + "            'last_execution_verification',\n"
    + response_indent
    + "            None,\n"
    + response_indent
    + "        )\n"
    + "\n"
    + response_indent
    + "    self._p10_4_run_evaluation(\n"
    + response_indent
    + "        goal=_p10_goal,\n"
    + response_indent
    + "        plan=_p10_plan,\n"
    + response_indent
    + "        result=_p10_result,\n"
    + response_indent
    + "    )\n"
    + response_indent
    + "except Exception:\n"
    + response_indent
    + "    self.last_p10_evaluation = None\n"
    + "\n"
)

patched = (
    patched[:response_pos]
    + evaluation_block
    + patched[response_pos:]
)

print(
    "P10 EVALUATION CALL: PASS"
)


# =========================================================
# STRUCTURAL VALIDATION
# =========================================================

if patched.count(
    "from __future__ import annotations"
) != original.count(
    "from __future__ import annotations"
):
    fail(
        "__future__ IMPORT COUNT CHANGED"
    )

for marker in [
    "self.p10_risk",
    "self.p10_simulator",
    "self.p10_judge",
    "self.last_p10_evaluation",
]:
    if marker not in patched:
        fail(
            "MISSING: " + marker
        )

print(
    "STRUCTURAL GUARDS: PASS"
)


# =========================================================
# AST
# =========================================================

parse_ast(
    patched,
    "PATCHED AST VALIDATION",
)

print(
    "PATCHED AST VALIDATION: PASS"
)


# =========================================================
# COMPILER VALIDATION
# =========================================================

TEMP.write_text(
    patched,
    encoding="utf-8",
)

try:
    compile_source(
        patched,
        str(TEMP),
    )

except Exception as exc:
    print()
    print(
        "PATCHED COMPILER VALIDATION: FAIL"
    )
    print(
        "MAIN.PY WAS NOT MODIFIED."
    )

    print()
    print(
        "=== IMPORTANT GENERATED SOURCE LINES ==="
    )

    for number, line in enumerate(
        patched.splitlines(),
        1,
    ):
        if (
            "from __future__ import" in line
            or "P10-4" in line
            or "# RESPONSE GUARD" in line
        ):
            print(
                f"{number:04d}: {line}"
            )

    print(
        "=== END DIAGNOSTIC ==="
    )

    raise RuntimeError(
        "PATCHED SOURCE COMPILER ERROR: "
        + str(exc)
    )

finally:
    TEMP.unlink(
        missing_ok=True
    )

print(
    "PATCHED COMPILER VALIDATION: PASS"
)


# =========================================================
# BACKUP
# =========================================================

shutil.copy2(
    MAIN,
    BACKUP,
)

print(
    "BACKUP CREATED:",
    BACKUP.name,
)


# =========================================================
# WRITE
# =========================================================

MAIN.write_text(
    patched,
    encoding="utf-8",
)

print(
    "MAIN.PY WRITE: PASS"
)


# =========================================================
# FINAL COMPILE
# =========================================================

try:
    compile_file(
        MAIN
    )

except Exception:
    shutil.copy2(
        BACKUP,
        MAIN,
    )

    print(
        "FINAL COMPILE: FAIL — ROLLBACK PASS"
    )

    raise

print(
    "FINAL COMPILE: PASS"
)


# =========================================================
# FINAL AST + SOURCE
# =========================================================

final_source = MAIN.read_text(
    encoding="utf-8"
)

for marker in [
    MARKER,
    "self.p10_risk",
    "self.p10_simulator",
    "self.p10_judge",
    "self.last_p10_evaluation",
    "_p10_4_run_evaluation",
    "_p10_4_get_evaluation_status",
    "P10-4 EVALUATION — ADVISORY ONLY",
]:
    if marker not in final_source:
        shutil.copy2(
            BACKUP,
            MAIN,
        )

        fail(
            "FINAL MARKER MISSING: "
            + marker
        )

assert_future_import_order(
    final_source
)

print(
    "FINAL MARKERS: PASS"
)

try:
    ast.parse(
        final_source
    )
except SyntaxError as exc:
    shutil.copy2(
        BACKUP,
        MAIN,
    )

    fail(
        "FINAL AST FAILED: "
        + str(exc)
    )

print(
    "FINAL AST: PASS"
)


# =========================================================
# IMPORT
# =========================================================

if str(ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT),
    )

try:
    import main as main_module

except Exception:
    shutil.copy2(
        BACKUP,
        MAIN,
    )

    print(
        "MAIN IMPORT: FAIL — ROLLBACK PASS"
    )

    raise

print(
    "MAIN IMPORT: PASS"
)


# =========================================================
# MINH
# =========================================================

if not hasattr(
    main_module,
    "MINH",
):
    shutil.copy2(
        BACKUP,
        MAIN,
    )

    fail(
        "GLOBAL MINH INSTANCE MISSING"
    )

print(
    "GLOBAL MINH: PASS"
)

instance = main_module.MINH


# =========================================================
# P10 INSTANCE
# =========================================================

for attr in [
    "p10_risk",
    "p10_simulator",
    "p10_judge",
    "last_p10_evaluation",
]:
    if not hasattr(
        instance,
        attr,
    ):
        shutil.copy2(
            BACKUP,
            MAIN,
        )

        fail(
            f"P10 INSTANCE MISSING: {attr}"
        )

print(
    "P10 INSTANCES: PASS"
)


# =========================================================
# STATUS
# =========================================================

if not hasattr(
    instance,
    "_p10_4_get_evaluation_status",
):
    shutil.copy2(
        BACKUP,
        MAIN,
    )

    fail(
        "P10 STATUS HELPER MISSING"
    )

status = instance._p10_4_get_evaluation_status()

if not isinstance(
    status,
    dict,
):
    shutil.copy2(
        BACKUP,
        MAIN,
    )

    fail(
        "P10 STATUS RESULT INVALID"
    )

print(
    "P10 STATUS: PASS"
)


# =========================================================
# RUNTIME
# =========================================================

try:
    result = instance._p10_4_run_evaluation(
        goal=None,
        plan=None,
        result={},
    )

except Exception:
    shutil.copy2(
        BACKUP,
        MAIN,
    )

    print(
        "P10 RUNTIME SMOKE: FAIL — ROLLBACK PASS"
    )

    raise

if not isinstance(
    result,
    dict,
):
    shutil.copy2(
        BACKUP,
        MAIN,
    )

    fail(
        "P10 RUNTIME RESULT INVALID"
    )

for key in [
    "risk",
    "simulator",
    "judge",
]:
    if key not in result:
        shutil.copy2(
            BACKUP,
            MAIN,
        )

        fail(
            f"P10 RUNTIME KEY MISSING: {key}"
        )

print(
    "P10 RUNTIME SMOKE: PASS"
)


# =========================================================
# SUCCESS
# =========================================================

print()
print(
    "============================================================"
)
print(
    "P10-4 INTEGRATION: PASS"
)
print(
    "RISK + SIMULATOR + JUDGE: IN MAIN"
)
print(
    "EXECUTION PATH: UNCHANGED"
)
print(
    "P10 MODE: ADVISORY ONLY"
)
print(
    "============================================================"
)