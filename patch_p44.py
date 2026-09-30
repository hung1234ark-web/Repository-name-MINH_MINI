import ast
import shutil
from pathlib import Path

MAIN = Path("main.py")
BACKUP = Path("main_execution_contract_p44_before.py")

print("=== P4-4 EXECUTION CONTRACT -> MAIN ===")

# ============================================================
# 1. READ + ORIGINAL AST
# ============================================================

source = MAIN.read_text(encoding="utf-8")
tree = ast.parse(source)

print("ORIGINAL AST: PASS")

# ============================================================
# 2. FIND MinhMiniCore
# ============================================================

classes = [
    node for node in tree.body
    if isinstance(node, ast.ClassDef)
    and node.name == "MinhMiniCore"
]

if len(classes) != 1:
    raise RuntimeError(
        f"MinhMiniCore count = {len(classes)}, expected 1"
    )

core = classes[0]

print("MinhMiniCore: FOUND")

# ============================================================
# 3. FIND __init__ + process
# ============================================================

init_nodes = [
    node for node in core.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "__init__"
]

process_nodes = [
    node for node in core.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "process"
]

if len(init_nodes) != 1:
    raise RuntimeError(
        f"__init__ count = {len(init_nodes)}, expected 1"
    )

if len(process_nodes) != 1:
    raise RuntimeError(
        f"process count = {len(process_nodes)}, expected 1"
    )

init_node = init_nodes[0]
process_node = process_nodes[0]

print(
    f"__init__(): "
    f"{init_node.lineno}-{init_node.end_lineno}"
)

print(
    f"process(): "
    f"{process_node.lineno}-{process_node.end_lineno}"
)

# ============================================================
# 4. VERIFY P4-2
# ============================================================

required_p42 = [
    "# META_ORCHESTRATOR_P42_INIT",
    "# META_ORCHESTRATOR_P42_ANALYZE",
    "self.meta_orchestrator.orchestrate(",
    "self.last_meta_orchestration = meta_result",
]

for marker in required_p42:
    if marker not in source:
        raise RuntimeError(
            "P4-2 foundation missing: " + marker
        )

print("P4-2 FOUNDATION: PASS")

# ============================================================
# 5. CHECK P4-4 DOES NOT ALREADY EXIST
# ============================================================

existing_markers = [
    "# EXECUTION_CONTRACT_P44_INIT",
    "# EXECUTION_CONTRACT_P44_BUILD",
    "# EXECUTION_CONTRACT_P44_GATE",
    "self.execution_contract_builder",
    "self.last_execution_contract",
]

for marker in existing_markers:
    if marker in source:
        raise RuntimeError(
            "P4-4 already appears integrated: " + marker
        )

print("P4-4 EXISTING CHECK: PASS")

# ============================================================
# 6. FIND INIT LAST META RESULT
# ============================================================

lines = source.splitlines()

init_start = init_node.lineno - 1
init_end = init_node.end_lineno

init_lines = lines[init_start:init_end]

meta_init_indexes = [
    i for i, line in enumerate(init_lines)
    if "self.last_meta_orchestration = None" in line
]

if len(meta_init_indexes) != 1:
    raise RuntimeError(
        "Could not uniquely locate "
        "self.last_meta_orchestration = None"
    )

meta_init_index = meta_init_indexes[0]
meta_init_line = init_lines[meta_init_index]

indent = (
    meta_init_line[
        :len(meta_init_line)
        - len(meta_init_line.lstrip())
    ]
)

init_block = [
    "",
    indent + "# EXECUTION_CONTRACT_P44_INIT",
    indent + "try:",
    indent + "    from execution_contract import create_execution_contract_builder",
    indent + "    self.execution_contract_builder = create_execution_contract_builder()",
    indent + "except Exception as exc:",
    indent + "    self.execution_contract_builder = None",
    indent + '    log("EXECUTION CONTRACT INIT ERROR: " + repr(exc))',
    "",
    indent + "# EXECUTION_CONTRACT_P44_LAST_RESULT_INIT",
    indent + "self.last_execution_contract = None",
]

# ============================================================
# 7. APPLY INIT PATCH
# ============================================================

absolute_init_insert = (
    init_start
    + meta_init_index
    + 1
)

new_lines = list(lines)

new_lines[
    absolute_init_insert:absolute_init_insert
] = init_block

temp_source = "\n".join(new_lines) + "\n"
ast.parse(temp_source)

print("INIT PATCH AST: PASS")

# ============================================================
# 8. RE-FIND PROCESS AFTER INIT PATCH
# ============================================================

temp_lines = temp_source.splitlines()
temp_tree = ast.parse(temp_source)

temp_core = [
    node for node in temp_tree.body
    if isinstance(node, ast.ClassDef)
    and node.name == "MinhMiniCore"
][0]

temp_process = [
    node for node in temp_core.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "process"
][0]

process_start = temp_process.lineno - 1
process_end = temp_process.end_lineno

process_lines = temp_lines[
    process_start:process_end
]

# ============================================================
# 9. FIND META ANALYZE BLOCK
# ============================================================

meta_analyze_indexes = [
    i for i, line in enumerate(process_lines)
    if "# META_ORCHESTRATOR_P42_ANALYZE" in line
]

if len(meta_analyze_indexes) != 1:
    raise RuntimeError(
        "Could not uniquely locate "
        "# META_ORCHESTRATOR_P42_ANALYZE"
    )

meta_analyze_index = meta_analyze_indexes[0]

# ============================================================
# 10. FIND NEEDS CLARIFICATION
# ============================================================

needs_indexes = [
    i for i, line in enumerate(process_lines)
    if "needs_clarification = bool(" in line
    and i > meta_analyze_index
]

if len(needs_indexes) != 1:
    raise RuntimeError(
        "Could not uniquely locate needs_clarification"
    )

needs_index = needs_indexes[0]
needs_line = process_lines[needs_index]

process_indent = (
    needs_line[
        :len(needs_line)
        - len(needs_line.lstrip())
    ]
)

# ============================================================
# 11. BUILD CONTRACT
# ============================================================

contract_block = [
    process_indent + "# EXECUTION_CONTRACT_P44_BUILD",
    process_indent + "execution_contract = None",
    process_indent + "if self.execution_contract_builder is not None:",
    process_indent + "    try:",
    process_indent + "        execution_contract = self.execution_contract_builder.build(",
    process_indent + "            completed,",
    process_indent + "            meta_result,",
    process_indent + "        )",
    process_indent + "        self.last_execution_contract = execution_contract",
    process_indent + "    except Exception as exc:",
    process_indent + "        self.last_execution_contract = None",
    process_indent + "        execution_contract = None",
    process_indent + "        log(",
    process_indent + '            "EXECUTION CONTRACT BUILD ERROR: "',
    process_indent + "            + repr(exc)",
    process_indent + "        )",
    "",
]

# Insert contract immediately BEFORE needs_clarification.
absolute_contract_insert = (
    process_start
    + needs_index
)

new_lines[
    absolute_contract_insert:absolute_contract_insert
] = contract_block

# ============================================================
# 12. REPARSE + FIND NEEDS CLARIFICATION AGAIN
# ============================================================

patched_temp = "\n".join(new_lines) + "\n"
patched_tree = ast.parse(patched_temp)

patched_core = [
    node for node in patched_tree.body
    if isinstance(node, ast.ClassDef)
    and node.name == "MinhMiniCore"
][0]

patched_process = [
    node for node in patched_core.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "process"
][0]

patched_process_start = patched_process.lineno - 1
patched_process_end = patched_process.end_lineno

patched_process_lines = temp_lines = patched_temp.splitlines()[
    patched_process_start:patched_process_end
]

patched_needs_indexes = [
    i for i, line in enumerate(patched_process_lines)
    if "needs_clarification = bool(" in line
]

if len(patched_needs_indexes) != 1:
    raise RuntimeError(
        "Could not uniquely relocate needs_clarification"
    )

patched_needs_index = patched_needs_indexes[0]

# ============================================================
# 13. ADD EXECUTION CONTRACT GATE
# ============================================================

# We do NOT replace the existing clarification logic.
# We only add a separate boolean that can feed into it.

needs_line = patched_process_lines[
    patched_needs_index
]

gate_indent = (
    needs_line[
        :len(needs_line)
        - len(needs_line.lstrip())
    ]
)

gate_block = [
    gate_indent + "# EXECUTION_CONTRACT_P44_GATE",
    gate_indent + "contract_blocks_execution = False",
    gate_indent + "if execution_contract is not None:",
    gate_indent + "    contract_intent = get_decision_value(",
    gate_indent + "        decision,",
    gate_indent + "        'intent',",
    gate_indent + "        '',",
    gate_indent + "    )",
    gate_indent + "    if (",
    gate_indent + "        contract_intent in {",
    gate_indent + "            'action',",
    gate_indent + "            'web',",
    gate_indent + "            'memory',",
    gate_indent + "            'time',",
    gate_indent + "            'date',",
    gate_indent + "        }",
    gate_indent + "        and not execution_contract.allowed",
    gate_indent + "    ):",
    gate_indent + "        contract_blocks_execution = True",
    gate_indent + "",
]

# Insert immediately before existing needs_clarification.
absolute_gate_insert = (
    patched_process_start
    + patched_needs_index
)

new_lines[
    absolute_gate_insert:absolute_gate_insert
] = gate_block

# ============================================================
# 14. MODIFY EXISTING CLARIFICATION BOOLEAN SURGICALLY
# ============================================================

final_source = "\n".join(new_lines) + "\n"

final_tree = ast.parse(final_source)

final_core = [
    node for node in final_tree.body
    if isinstance(node, ast.ClassDef)
    and node.name == "MinhMiniCore"
][0]

final_process = [
    node for node in final_core.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "process"
][0]

final_start = final_process.lineno - 1
final_end = final_process.end_lineno

final_lines = final_source.splitlines()

process_section = final_lines[
    final_start:final_end
]

target_indexes = [
    i for i, line in enumerate(process_section)
    if "needs_clarification = bool(" in line
]

if len(target_indexes) != 1:
    raise RuntimeError(
        "Final needs_clarification target not unique"
    )

target_index = target_indexes[0]

# Locate closing ')' of existing bool expression.
close_index = None

for i in range(target_index, len(process_section)):
    if process_section[i].strip() == ")":
        close_index = i
        break

if close_index is None:
    raise RuntimeError(
        "Could not locate end of needs_clarification expression"
    )

# The original expression is preserved and wrapped.
original_expr = process_section[
    target_index:close_index + 1
]

original_indent = process_section[
    target_index
][
    :len(process_section[target_index])
    - len(process_section[target_index].lstrip())
]

replacement = []

for i, line in enumerate(original_expr):
    if i == 0:
        replacement.append(
            original_indent
            + "needs_clarification = bool("
        )
    elif i == len(original_expr) - 1:
        replacement.append(
            original_indent
            + "    contract_blocks_execution"
            + "\n"
            + original_indent
            + ")"
        )
    else:
        replacement.append(line)

# Better and safer: reconstruct the expression from the original
# body without changing its existing contents.
body_lines = original_expr[1:-1]

replacement = [
    original_indent + "needs_clarification = bool(",
]

replacement.extend(body_lines)

replacement.append(
    original_indent
    + "    or contract_blocks_execution"
)

replacement.append(
    original_indent + ")"
)

absolute_target_start = final_start + target_index
absolute_target_end = final_start + close_index + 1

final_lines[
    absolute_target_start:absolute_target_end
] = replacement

final_source = "\n".join(final_lines) + "\n"

# ============================================================
# 15. FINAL AST
# ============================================================

ast.parse(final_source)

print("FINAL AST: PASS")

# ============================================================
# 16. MARKER CHECK
# ============================================================

required_markers = [
    "# EXECUTION_CONTRACT_P44_INIT",
    "# EXECUTION_CONTRACT_P44_LAST_RESULT_INIT",
    "# EXECUTION_CONTRACT_P44_BUILD",
    "# EXECUTION_CONTRACT_P44_GATE",
    "self.execution_contract_builder",
    "self.execution_contract_builder.build(",
    "self.last_execution_contract = execution_contract",
    "contract_blocks_execution",
]

for marker in required_markers:
    if marker not in final_source:
        raise RuntimeError(
            "MARKER CHECK FAILED: " + marker
        )

    print(
        "CHECK:",
        marker,
        "= PASS",
    )

# ============================================================
# 17. BACKUP
# ============================================================

shutil.copy2(MAIN, BACKUP)

if not BACKUP.exists():
    raise RuntimeError(
        "Backup creation failed"
    )

print("BACKUP: PASS")
print("BACKUP FILE:", BACKUP.name)

# ============================================================
# 18. WRITE
# ============================================================

MAIN.write_text(
    final_source,
    encoding="utf-8",
)

print("PATCH STATUS: PASS")
print("MAIN.PY UPDATED")
print("BACKUP:", BACKUP.name)
