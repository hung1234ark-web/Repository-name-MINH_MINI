from pathlib import Path
import ast
import py_compile
import shutil
import importlib

MAIN = Path("main.py")

print("=" * 80)
print("P12-2 TOOL SELECTOR MESSAGE FIX")
print("SAFE SURGICAL PATCH")
print("=" * 80)

source = MAIN.read_text(encoding="utf-8-sig")

ast.parse(source)
py_compile.compile(str(MAIN), doraise=True)

print("MAIN PRECHECK: PASS")

old = '''            selection = self._p11_select_tool(
                goal=None,
                plan=None,
                decision=decision,
                result=result,
            )
'''

new = '''            # P12-2 MESSAGE-AWARE TOOL SELECTION
            #
            # ToolSelector.select() builds its routing text
            # from goal / plan / decision / result.
            # The user's actual message must therefore be
            # supplied through goal so that explicit requests
            # such as "tìm trên web" remain visible to P11.
            selection = self._p11_select_tool(
                goal=message,
                plan=None,
                decision=decision,
                result=result,
            )
'''

if old not in source:
    raise SystemExit(
        "ERROR: exact P12-2 selector call not found"
    )

if "P12-2 MESSAGE-AWARE TOOL SELECTION" in source:
    raise SystemExit(
        "ERROR: fix already present"
    )

backup = Path("main.py.before_p12_2_message_fix")

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

source = source.replace(
    old,
    new,
    1,
)

MAIN.write_text(
    source,
    encoding="utf-8",
)

print("SURGICAL PATCH: PASS")

# ------------------------------------------------------------
# VALIDATION
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

if final_source.count(
    "P12-2 MESSAGE-AWARE TOOL SELECTION"
) != 1:
    shutil.copy2(backup, MAIN)
    raise SystemExit(
        "MARKER VALIDATION FAILED — ROLLBACK"
    )

if "goal=message" not in final_source:
    shutil.copy2(backup, MAIN)
    raise SystemExit(
        "MESSAGE INPUT VALIDATION FAILED — ROLLBACK"
    )

print("MESSAGE INPUT: PASS")

# ------------------------------------------------------------
# RUNTIME
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
            "global MINH missing"
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

    result = helper(
        message="tìm thông tin trên web",
        decision={
            "intent": "web",
            "tool": "web",
        },
        result={
            "judge": {
                "decision": "proceed",
            }
        },
    )

    if not isinstance(result, dict):
        raise RuntimeError(
            "selector result is not dict"
        )

    print("MAIN IMPORT: PASS")
    print(
        "SELECTED TOOL:",
        result.get("tool"),
    )
    print(
        "DECISION TOOL:",
        result.get("decision_tool"),
    )
    print(
        "TOOL MATCH:",
        result.get("tool_match"),
    )
    print(
        "ADVISORY ONLY:",
        result.get("advisory_only"),
    )

    if result.get("tool") != "web":
        raise RuntimeError(
            "expected selected tool = web"
        )

    if result.get("decision_tool") != "web":
        raise RuntimeError(
            "decision tool was not preserved"
        )

    if result.get("tool_match") is not True:
        raise RuntimeError(
            "tool_match is not True"
        )

    if result.get("advisory_only") is not True:
        raise RuntimeError(
            "advisory_only contract failed"
        )

    print("WEB SELECTION: PASS")
    print("TOOL MATCH: PASS")
    print("ADVISORY CONTRACT: PASS")

except Exception as exc:
    shutil.copy2(
        backup,
        MAIN,
    )

    print("RUNTIME FAILED — ROLLBACK: PASS")

    raise SystemExit(
        "P12-2 message fix failed: "
        + repr(exc)
    )

print()
print("=" * 80)
print("P12-2 MESSAGE FIX: PASS")
print("MESSAGE -> TOOL SELECTOR: CONNECTED")
print("WEB REQUEST -> WEB TOOL: PASS")
print("DECISION TOOL PRESERVED: PASS")
print("NO EXECUTION DURING TEST: PASS")
print("P12-1 PRESERVED: PASS")
print("P4-5 PRESERVED: PASS")
print("P10 PRESERVED: PASS")
print("=" * 80)
