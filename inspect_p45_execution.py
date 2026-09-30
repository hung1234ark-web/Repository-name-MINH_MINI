from pathlib import Path
import ast

MAIN = Path("main.py")
SOURCE = MAIN.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)

print("=== P4-5 EXECUTION / VERIFY FOUNDATION DIAGNOSTIC ===")

# ============================================================
# 1. FIND MinhMiniCore
# ============================================================

core = None

for node in TREE.body:
    if isinstance(node, ast.ClassDef) and node.name == "MinhMiniCore":
        core = node
        break

if core is None:
    raise RuntimeError("Không tìm thấy class MinhMiniCore")

print("MinhMiniCore: FOUND")

# ============================================================
# 2. FIND METHODS
# ============================================================

methods = {}

for node in core.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        methods[node.name] = node

required_methods = [
    "process",
    "execute_decision",
]

for name in required_methods:
    if name in methods:
        node = methods[name]
        print(
            f"{name}(): "
            f"{node.lineno}-{getattr(node, 'end_lineno', '?')} = FOUND"
        )
    else:
        print(f"{name}() = MISSING")

# ============================================================
# 3. EXECUTE_DECISION SOURCE
# ============================================================

execute_node = methods.get("execute_decision")

if execute_node is None:
    raise RuntimeError(
        "Không tìm thấy MinhMiniCore.execute_decision()"
    )

execute_source = ast.get_source_segment(
    SOURCE,
    execute_node,
)

if not execute_source:
    raise RuntimeError(
        "Không đọc được source execute_decision()"
    )

print("")
print("=== EXECUTE_DECISION MARKERS ===")

markers = [
    "execution_result",
    "success",
    "error",
    "execute",
]

for marker in markers:
    found = marker in execute_source
    print(
        f"CHECK: {marker} = "
        + ("PASS" if found else "MISSING")
    )

# ============================================================
# 4. PROCESS RESULT FLOW
# ============================================================

process_node = methods.get("process")

if process_node is None:
    raise RuntimeError(
        "Không tìm thấy MinhMiniCore.process()"
    )

process_source = ast.get_source_segment(
    SOURCE,
    process_node,
)

print("")
print("=== PROCESS RESULT FLOW ===")

process_markers = [
    "execution_result",
    "self.execute_decision(",
    "guard_answer(",
    "update_context(",
    "add_history(",
]

for marker in process_markers:
    found = marker in process_source
    print(
        f"CHECK: {marker} = "
        + ("PASS" if found else "MISSING")
    )

# ============================================================
# 5. CONTRACT VERIFY FLOW
# ============================================================

print("")
print("=== EXECUTION CONTRACT VERIFY ===")

contract_markers = [
    "self.last_execution_contract",
    "execution_contract.allowed",
    "verify_required",
]

for marker in contract_markers:
    found = marker in process_source
    print(
        f"CHECK: {marker} = "
        + ("PASS" if found else "MISSING")
    )

# ============================================================
# 6. IMPORTANT: DO NOT MODIFY
# ============================================================

print("")
print("SOURCE MODIFIED: NO")
print("BACKUP CREATED: NO")
print("")
print("=== P4-5 FOUNDATION DIAGNOSTIC DONE ===")
