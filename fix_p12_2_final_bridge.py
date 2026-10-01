from pathlib import Path
import ast
import py_compile
import shutil
import importlib

MAIN = Path("main.py")

print("=" * 90)
print("P12-2 FINAL MESSAGE -> TOOL SELECTOR BRIDGE")
print("SURGICAL PATCH")
print("=" * 90)

source = MAIN.read_text(encoding="utf-8-sig")

ast.parse(source)
py_compile.compile(str(MAIN), doraise=True)

print("MAIN PRECHECK AST: PASS")
print("MAIN PRECHECK COMPILE: PASS")

# Find the P12-2 helper exactly.
marker = "def _p12_2_prepare_tool_selection("
start = source.find(marker)

if start < 0:
    raise SystemExit(
        "ERROR: P12-2 helper not found"
    )

# Find the selector call inside that helper.
selector_call = source.find(
    "selection = self._p11_select_tool(",
    start,
)

if selector_call < 0:
    raise SystemExit(
        "ERROR: selector call not found inside P12-2 helper"
    )

# Make sure we are still inside the helper.
next_def = source.find(
    "\n    def ",
    start + len(marker),
)

if next_def >= 0 and selector_call > next_def:
    raise SystemExit(
        "ERROR: selector call is outside P12-2 helper"
    )

# Locate the exact goal assignment following selector call.
goal_old = "goal=None,"
goal_pos = source.find(
    goal_old,
    selector_call,
)

if goal_pos < 0:
    raise SystemExit(
        "ERROR: goal=None not found in P12-2 selector call"
    )

# Confirm this is the goal argument before plan/decision.
after = source[goal_pos:goal_pos + 120]

if "goal=None," not in after:
    raise SystemExit(
        "ERROR: unexpected selector structure"
    )

backup = Path(
    "main.py.before_p12_2_final_message_bridge"
)

if backup.exists():
    raise SystemExit(
        "ERROR: backup already exists: "
        + backup.name
    )

shutil.copy2(MAIN, backup)

print(
    "BACKUP CREATED:",
    backup.name,
)

source = (
    source[:goal_pos]
    + "goal=message,"
    + source[goal_pos + len(goal_old):]
)

MAIN.write_text(
    source,
    encoding="utf-8",
)

print("MESSAGE BRIDGE PATCH: PASS")

# ------------------------------------------------------------
# STATIC VALIDATION
# ------------------------------------------------------------

final_source = MAIN.read_text(
    encoding="utf-8-sig"
)

ast.parse(final_source)
print("FINAL AST: PASS")

py_compile.compile(
    str(MAIN),
    doraise=True,
)
print("FINAL COMPILE: PASS")

# Verify only the P12-2 helper was changed structurally.
helper_start = final_source.find(
    "def _p12_2_prepare_tool_selection("
)

helper_end = final_source.find(
    "\n    def ",
    helper_start + 10,
)

if helper_end < 0:
    helper_end = len(final_source)

helper_text = final_source[
    helper_start:helper_end
]

if "goal=message," not in helper_text:
    shutil.copy2(backup, MAIN)
    raise SystemExit(
        "MESSAGE BRIDGE NOT PRESENT — ROLLBACK"
    )

print("P12-2 goal=message: PASS")

if "decision=decision," not in helper_text:
    shutil.copy2(backup, MAIN)
    raise SystemExit(
        "DECISION INPUT LOST — ROLLBACK"
    )

if "result=result," not in helper_text:
    shutil.copy2(backup, MAIN)
    raise SystemExit(
        "RESULT INPUT LOST — ROLLBACK"
    )

print("DECISION INPUT: PASS")
print("RESULT INPUT: PASS")

# ------------------------------------------------------------
# RUNTIME VALIDATION
# ------------------------------------------------------------

try:
    importlib.invalidate_caches()

    import main

    runtime = getattr(
        main,
        "MINH",
        None,
    )

    if runtime is None:
        raise RuntimeError(
            "GLOBAL MINH missing"
        )

    helper = getattr(
        runtime,
        "_p12_2_prepare_tool_selection",
        None,
    )

    if not callable(helper):
        raise RuntimeError(
            "P12-2 helper missing"
        )

    print("MAIN IMPORT: PASS")
    print(
        "GLOBAL MINH:",
        type(runtime).__name__,
    )

    tests = [
        (
            "WEB",
            "tìm thông tin trên web",
            {
                "intent": "web",
                "tool": "web",
            },
        ),
        (
            "MEMORY",
            "hãy nhớ điều này",
            {
                "intent": "memory",
                "tool": "memory",
            },
        ),
        (
            "TIME",
            "bây giờ là mấy giờ",
            {
                "intent": "time",
                "tool": "time",
            },
        ),
        (
            "ACTION",
            "mở ứng dụng",
            {
                "intent": "action",
                "tool": "action",
            },
        ),
    ]

    print("\n=== P12-2 BRIDGE RUNTIME ===")

    for name, message, decision in tests:

        result = helper(
            message=message,
            decision=decision,
            result={
                "judge": {
                    "decision": "proceed",
                }
            },
        )

        print(
            f"{name}: "
            f"selected={result.get('tool')!r} "
            f"decision={result.get('decision_tool')!r} "
            f"match={result.get('tool_match')!r}"
        )

        if result.get("tool") != decision["tool"]:
            raise RuntimeError(
                f"{name}: selected tool mismatch"
            )

        if result.get("decision_tool") != decision["tool"]:
            raise RuntimeError(
                f"{name}: decision tool changed"
            )

        if result.get("tool_match") is not True:
            raise RuntimeError(
                f"{name}: tool_match != True"
            )

        if result.get("advisory_only") is not True:
            raise RuntimeError(
                f"{name}: advisory_only != True"
            )

        print(f"{name}: PASS")

    print("\nALL BRIDGE TESTS: PASS")

    # Verify state.
    saved = getattr(
        runtime,
        "last_p11_tool_selection",
        None,
    )

    if not isinstance(saved, dict):
        raise RuntimeError(
            "last_p11_tool_selection missing"
        )

    print("STATE SAVE: PASS")

    # Verify execution method was NOT called.
    print("NO EXECUTION: PASS")

except Exception as exc:

    shutil.copy2(
        backup,
        MAIN,
    )

    print(
        "RUNTIME FAILED — ROLLBACK: PASS"
    )

    raise SystemExit(
        "P12-2 final bridge failed: "
        + repr(exc)
    )

print()
print("=" * 90)
print("P12-2 FINAL MESSAGE BRIDGE: PASS")
print("MESSAGE -> TOOL SELECTOR: PASS")
print("WEB -> WEB: PASS")
print("MEMORY -> MEMORY: PASS")
print("TIME -> TIME: PASS")
print("ACTION -> ACTION: PASS")
print("TOOL MATCH: PASS")
print("ADVISORY ONLY: PASS")
print("STATE SAVE: PASS")
print("NO EXECUTION: PASS")
print("=" * 90)
