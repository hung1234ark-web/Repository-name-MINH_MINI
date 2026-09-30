import ast
from pathlib import Path
import shutil

MAIN = Path("main.py")
BACKUP = Path("main_meta_orchestrator_p42_before.py")

print("=== P4-2 META-ORCHESTRATOR INTEGRATION ===")

# ------------------------------------------------------------
# 1. READ + AST CHECK
# ------------------------------------------------------------

source = MAIN.read_text(encoding="utf-8")
tree = ast.parse(source)

print("ORIGINAL AST: PASS")

# ------------------------------------------------------------
# 2. FIND MinhMiniCore
# ------------------------------------------------------------

classes = [
    node
    for node in tree.body
    if isinstance(node, ast.ClassDef)
    and node.name == "MinhMiniCore"
]

if len(classes) != 1:
    raise RuntimeError(
        f"MinhMiniCore count = {len(classes)}, expected 1"
    )

core = classes[0]

print("MinhMiniCore: FOUND")

# ------------------------------------------------------------
# 3. FIND __init__ AND process()
# ------------------------------------------------------------

init_methods = [
    node
    for node in core.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "__init__"
]

process_methods = [
    node
    for node in core.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "process"
]

if len(init_methods) != 1:
    raise RuntimeError(
        f"__init__ count = {len(init_methods)}, expected 1"
    )

if len(process_methods) != 1:
    raise RuntimeError(
        f"process count = {len(process_methods)}, expected 1"
    )

init_node = init_methods[0]
process_node = process_methods[0]

print(
    f"__init__(): line "
    f"{init_node.lineno} - {init_node.end_lineno}"
)

print(
    f"process(): line "
    f"{process_node.lineno} - {process_node.end_lineno}"
)

# ------------------------------------------------------------
# 4. CHECK P3-2 EXISTS
# ------------------------------------------------------------

required_p32_markers = [
    "# THINK_X_P32_INIT",
    "# THINK_X_P32_ANALYZE",
    "self.think_x.think(",
    "self.last_think_x = think_result",
]

for marker in required_p32_markers:
    if marker not in source:
        raise RuntimeError(
            "P3-2 marker missing: " + marker
        )

print("P3-2 FOUNDATION: PASS")

# ------------------------------------------------------------
# 5. CHECK P4 DOES NOT ALREADY EXIST
# ------------------------------------------------------------

p4_markers = [
    "# META_ORCHESTRATOR_P42_INIT",
    "# META_ORCHESTRATOR_P42_ANALYZE",
    "self.meta_orchestrator",
    "self.last_meta_orchestration",
]

for marker in p4_markers:
    if marker in source:
        raise RuntimeError(
            "P4-2 appears already integrated: " + marker
        )

print("P4-2 EXISTING CHECK: PASS")

# ------------------------------------------------------------
# 6. FIND INIT INSERTION POINT
# ------------------------------------------------------------

lines = source.splitlines()

init_start = init_node.lineno - 1
init_end = init_node.end_lineno

init_lines = lines[init_start:init_end]

last_think_x_indexes = [
    i
    for i, line in enumerate(init_lines)
    if "self.last_think_x = None" in line
]

if len(last_think_x_indexes) != 1:
    raise RuntimeError(
        "Could not uniquely locate self.last_think_x = None"
    )

last_think_x_index = last_think_x_indexes[0]

original_init_line = init_lines[last_think_x_index]

indent = original_init_line[
    : len(original_init_line)
    - len(original_init_line.lstrip())
]

init_block = [
    "",
    indent + "# META_ORCHESTRATOR_P42_INIT",
    indent + "try:",
    indent + "    from meta_orchestrator import create_meta_orchestrator",
    indent + "    self.meta_orchestrator = create_meta_orchestrator()",
    indent + "except Exception as exc:",
    indent + "    self.meta_orchestrator = None",
    indent + '    log("META ORCHESTRATOR INIT ERROR: " + repr(exc))',
    indent + "",
    indent + "# META_ORCHESTRATOR_P42_LAST_RESULT_INIT",
    indent + "self.last_meta_orchestration = None",
]

# ------------------------------------------------------------
# 7. FIND PROCESS INSERTION POINT
# ------------------------------------------------------------

process_start = process_node.lineno - 1
process_end = process_node.end_lineno

process_lines = lines[process_start:process_end]

analyze_marker_indexes = [
    i
    for i, line in enumerate(process_lines)
    if "# THINK_X_P32_ANALYZE" in line
]

if len(analyze_marker_indexes) != 1:
    raise RuntimeError(
        "Could not uniquely locate # THINK_X_P32_ANALYZE"
    )

analyze_index = analyze_marker_indexes[0]

# Find the existing needs_clarification line AFTER THINK X.
needs_indexes = [
    i
    for i, line in enumerate(process_lines)
    if "needs_clarification = bool(" in line
    and i > analyze_index
]

if len(needs_indexes) != 1:
    raise RuntimeError(
        "Could not uniquely locate needs_clarification after THINK X"
    )

needs_index = needs_indexes[0]

needs_line = process_lines[needs_index]

process_indent = needs_line[
    : len(needs_line)
    - len(needs_line.lstrip())
]

# ------------------------------------------------------------
# 8. BUILD P4-2 ANALYZE BLOCK
# ------------------------------------------------------------

p4_process_block = [
    process_indent + "# META_ORCHESTRATOR_P42_ANALYZE",
    process_indent + "meta_result = None",
    process_indent + "if self.meta_orchestrator is not None:",
    process_indent + "    try:",
    process_indent + "        current_goal = None",
    process_indent + "        if hasattr(self, 'goal_manager'):",
    process_indent + "            getter = getattr(",
    process_indent + "                self.goal_manager,",
    process_indent + "                'get_current',",
    process_indent + "            )",
    process_indent + "            if callable(getter):",
    process_indent + "                current_goal = getter()",
    process_indent + "",
    process_indent + "        meta_result = self.meta_orchestrator.orchestrate(",
    process_indent + "            completed,",
    process_indent + "            decision,",
    process_indent + "            think_result,",
    process_indent + "            current_goal,",
    process_indent + "        )",
    process_indent + "        self.last_meta_orchestration = meta_result",
    process_indent + "    except Exception as exc:",
    process_indent + "        self.last_meta_orchestration = None",
    process_indent + "        log(",
    process_indent + '            "META ORCHESTRATOR ANALYZE ERROR: "',
    process_indent + "            + repr(exc)",
    process_indent + "        )",
    "",
]

# ------------------------------------------------------------
# 9. APPLY PATCH
# ------------------------------------------------------------

# INIT
absolute_init_index = init_start + last_think_x_index + 1

new_lines = list(lines)

new_lines[
    absolute_init_index:absolute_init_index
] = init_block

# PROCESS position must be recalculated after INIT insertion.
# Locate the unique process marker again in modified text.

temp_source = "\n".join(new_lines) + "\n"
temp_lines = temp_source.splitlines()

marker_positions = [
    i
    for i, line in enumerate(temp_lines)
    if "# META_ORCHESTRATOR_P42_INIT" in line
]

if len(marker_positions) != 1:
    raise RuntimeError(
        "Post-init marker validation failed"
    )

# Re-find process method using fresh AST.
temp_tree = ast.parse(temp_source)

temp_classes = [
    node
    for node in temp_tree.body
    if isinstance(node, ast.ClassDef)
    and node.name == "MinhMiniCore"
]

temp_core = temp_classes[0]

temp_process = [
    node
    for node in temp_core.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "process"
][0]

temp_process_start = temp_process.lineno - 1
temp_process_end = temp_process.end_lineno

temp_process_lines = temp_lines[
    temp_process_start:temp_process_end
]

temp_needs_indexes = [
    i
    for i, line in enumerate(temp_process_lines)
    if "needs_clarification = bool(" in line
]

if len(temp_needs_indexes) != 1:
    raise RuntimeError(
        "Post-init process marker validation failed"
    )

absolute_process_index = (
    temp_process_start
    + temp_needs_indexes[0]
)

new_lines[
    absolute_process_index:absolute_process_index
] = p4_process_block

patched_source = "\n".join(new_lines) + "\n"

# ------------------------------------------------------------
# 10. PATCHED AST CHECK BEFORE WRITE
# ------------------------------------------------------------

ast.parse(patched_source)

print("PATCHED AST: PASS")

# ------------------------------------------------------------
# 11. MARKER CHECK
# ------------------------------------------------------------

checks = [
    "# META_ORCHESTRATOR_P42_INIT",
    "# META_ORCHESTRATOR_P42_LAST_RESULT_INIT",
    "# META_ORCHESTRATOR_P42_ANALYZE",
    "self.meta_orchestrator = create_meta_orchestrator()",
    "self.meta_orchestrator.orchestrate(",
    "self.last_meta_orchestration = meta_result",
]

for marker in checks:
    if marker not in patched_source:
        raise RuntimeError(
            "PATCH CHECK FAILED: " + marker
        )

    print("CHECK:", marker, "= PASS")

# ------------------------------------------------------------
# 12. BACKUP
# ------------------------------------------------------------

shutil.copy2(MAIN, BACKUP)

if not BACKUP.exists():
    raise RuntimeError("Backup creation failed")

print("BACKUP: PASS")
print("BACKUP FILE:", BACKUP.name)

# ------------------------------------------------------------
# 13. WRITE
# ------------------------------------------------------------

MAIN.write_text(
    patched_source,
    encoding="utf-8",
)

print("PATCH STATUS: PASS")
print("MAIN.PY UPDATED")
print("BACKUP:", BACKUP.name)
