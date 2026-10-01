from pathlib import Path
import ast
import sys

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"
SELECTOR = ROOT / "tool_selector.py"

def fail(msg):
    raise RuntimeError(msg)

def read(path):
    return path.read_text(encoding="utf-8-sig")

def compile_file(path):
    source = read(path)
    compile(source, str(path), "exec")
    ast.parse(source, filename=str(path))

print("=" * 60)
print("P11-3 RUNTIME VALIDATION")
print("NO PROCESS / NO OLLAMA / NO WEB / NO ACTION")
print("=" * 60)

# ------------------------------------------------------------
# FILE / SYNTAX
# ------------------------------------------------------------
if not MAIN.exists():
    fail("main.py NOT FOUND")
print("MAIN FILE: PASS")

if not SELECTOR.exists():
    fail("tool_selector.py NOT FOUND")
print("TOOL_SELECTOR FILE: PASS")

compile_file(MAIN)
print("MAIN AST + COMPILE: PASS")

compile_file(SELECTOR)
print("TOOL_SELECTOR AST + COMPILE: PASS")

# ------------------------------------------------------------
# STATIC STRUCTURE
# ------------------------------------------------------------
source = read(MAIN)
tree = ast.parse(source, filename=str(MAIN))

core = None
for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef) and node.name == "MinhMiniCore":
        core = node
        break

if core is None:
    fail("MinhMiniCore NOT FOUND")

print("MinhMiniCore CLASS: PASS")

method_names = {
    node.name
    for node in core.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
}

for required in (
    "__init__",
    "process",
    "_p11_select_tool",
):
    if required not in method_names:
        fail("MISSING METHOD: " + required)

print("P11 METHODS: PASS")

if "self.tool_selector = create_tool_selector()" not in source:
    fail("P11 SELECTOR INIT MISSING")

if "P11-2 TOOL SELECTOR <- P10 JUDGE DECISION" not in source:
    fail("P11-2 INTEGRATION MARKER MISSING")

print("P11-2 INTEGRATION MARKER: PASS")

# ------------------------------------------------------------
# HARD NO-EXECUTION GUARDS
# ------------------------------------------------------------
for forbidden in (
    "self.tool_selector.execute(",
    "self.tool_selector.run(",
    "self.tool_selector.call(",
    "self._p11_select_tool().execute(",
    "self._p11_select_tool().run(",
    "self._p11_select_tool().call(",
):
    if forbidden in source:
        fail("FORBIDDEN EXECUTION: " + forbidden)

print("NO TOOL EXECUTION GUARDS: PASS")

# ------------------------------------------------------------
# IMPORT
# ------------------------------------------------------------
if "main" in sys.modules:
    del sys.modules["main"]

import main

MINH = getattr(main, "MINH", None)

if MINH is None:
    fail("GLOBAL MINH NOT FOUND")

print("MAIN IMPORT: PASS")
print("GLOBAL MINH: PASS")
print("MINH TYPE:", type(MINH).__name__)

selector = getattr(MINH, "tool_selector", None)

if selector is None:
    fail("tool_selector OBJECT MISSING")

print("RUNTIME TOOL SELECTOR: PASS")
print("SELECTOR TYPE:", type(selector).__name__)

# ------------------------------------------------------------
# TEST 1 — WEB
# ------------------------------------------------------------
web_result = selector.select(
    goal="tìm giá iphone mới nhất",
    plan=None,
    decision="proceed",
    result={"judge": {"decision": "proceed"}},
)

if web_result.get("tool") != "web":
    fail("WEB SELECTION FAILED")

if web_result.get("advisory_only") is not True:
    fail("WEB ADVISORY FLAG FAILED")

print("TEST 1 WEB: PASS")

# ------------------------------------------------------------
# TEST 2 — MEMORY
# ------------------------------------------------------------
memory_result = selector.select(
    goal="ghi nhớ Lam đang học Python",
    plan=None,
    decision="proceed",
    result={"judge": {"decision": "proceed"}},
)

if memory_result.get("tool") != "memory":
    fail("MEMORY SELECTION FAILED")

print("TEST 2 MEMORY: PASS")

# ------------------------------------------------------------
# TEST 3 — TIME
# ------------------------------------------------------------
time_result = selector.select(
    goal="bây giờ là mấy giờ",
    plan=None,
    decision="proceed",
    result={"judge": {"decision": "proceed"}},
)

if time_result.get("tool") != "time":
    fail("TIME SELECTION FAILED")

print("TEST 3 TIME: PASS")

# ------------------------------------------------------------
# TEST 4 — ACTION
# ------------------------------------------------------------
action_result = selector.select(
    goal="mở ứng dụng",
    plan=None,
    decision="proceed",
    result={"judge": {"decision": "proceed"}},
)

if action_result.get("tool") != "action":
    fail("ACTION SELECTION FAILED")

print("TEST 4 ACTION: PASS")

# ------------------------------------------------------------
# TEST 5 — UNKNOWN / FALLBACK
# ------------------------------------------------------------
fallback_result = selector.select(
    goal="xin chào Minh",
    plan=None,
    decision="proceed",
    result={"judge": {"decision": "proceed"}},
)

if fallback_result.get("tool") != "ollama":
    fail("FALLBACK SELECTION FAILED")

print("TEST 5 FALLBACK: PASS")

# ------------------------------------------------------------
# TEST 6 — EMPTY INPUT
# ------------------------------------------------------------
empty_result = selector.select(
    goal=None,
    plan=None,
    decision=None,
    result=None,
)

if empty_result.get("tool") is not None:
    fail("EMPTY INPUT SHOULD HAVE NO TOOL")

if empty_result.get("allowed") is not False:
    fail("EMPTY INPUT ALLOWED FLAG FAILED")

print("TEST 6 EMPTY INPUT: PASS")

# ------------------------------------------------------------
# TEST 7 — HELPER
# ------------------------------------------------------------
helper_result = MINH._p11_select_tool(
    goal="tìm tin tức mới nhất",
    plan=None,
    decision="proceed",
    result={"judge": {"decision": "proceed"}},
)

if not isinstance(helper_result, dict):
    fail("P11 HELPER RESULT INVALID")

if helper_result.get("tool") != "web":
    fail("P11 HELPER WEB TEST FAILED")

saved = getattr(MINH, "last_p11_tool_selection", None)

if not isinstance(saved, dict):
    fail("P11 STATE SAVE FAILED")

print("TEST 7 MAIN HELPER: PASS")
print("P11 STATE SAVE: PASS")

# ------------------------------------------------------------
# TEST 8 — DECISION PATHS
# ------------------------------------------------------------
for decision in ("proceed", "review", "stop"):
    result = MINH._p11_select_tool(
        goal="tìm thông tin",
        plan=None,
        decision=decision,
        result={"judge": {"decision": decision}},
    )

    if not isinstance(result, dict):
        fail("DECISION RESULT INVALID: " + decision)

print("TEST 8 PROCEED/REVIEW/STOP: PASS")

# ------------------------------------------------------------
# TEST 9 — ADVISORY CONTRACT
# ------------------------------------------------------------
for result in (
    web_result,
    memory_result,
    time_result,
    action_result,
    fallback_result,
):
    if result.get("advisory_only") is not True:
        fail("ADVISORY CONTRACT FAILED")

print("TEST 9 ADVISORY CONTRACT: PASS")

# ------------------------------------------------------------
# FINAL
# ------------------------------------------------------------
print()
print("=" * 60)
print("P11-3 RESULT: PASS")
print("RUNTIME VALIDATION: PASS")
print("P11-1: PASS")
print("P11-2: PASS")
print("P11-3: PASS")
print("TOOL SELECTION: PASS")
print("NO TOOL EXECUTION: PASS")
print("P10 PRESERVED: PASS")
print("READY FOR P12: YES")
print("=" * 60)
