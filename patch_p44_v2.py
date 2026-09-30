import ast
import shutil
from pathlib import Path

MAIN = Path("main.py")
BACKUP = Path("main_execution_contract_p44_before_v2.py")

print("=== P4-4 EXECUTION CONTRACT -> MAIN V2 ===")

# ============================================================
# 1. READ + AST CHECK
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
# 5. VERIFY P4-4 NOT ALREADY INTEGRATED
# ============================================================

p44_markers = [
    "# EXECUTION_CONTRACT_P44_INIT",
    "# EXECUTION_CONTRACT_P44_BUILD",
    "# EXECUTION_CONTRACT_P44_GATE",
]

for marker in p44_markers:
    if marker in source:
        raise RuntimeError(
            "P4-4 marker already exists: " + marker
        )

print("P4-4 EXISTING CHECK: PASS")

# ============================================================
# 6. WORK WITH LINES
# ============================================================

lines = source.splitlines()

# ============================================================
# 7. PATCH __init__
# ============================================================

init_start = init_node.lineno - 1
init_end = init_node.end_lineno

init_lines = lines[init_start:init_end]

meta_indexes = [
    i for i, line in enumerate(init_lines)
    if "self.last_meta_orchestration = None" in line
]

if len(meta_indexes) != 1:
    raise RuntimeError(
        "Cannot uniquely locate "
        "self.last_meta_orchestration = None"
    )

meta_index = meta_indexes[0]

meta_line = init_lines[meta_index]

indent = (
    meta_line[
        :len(meta_line)
        - len(meta_line.lstrip())
    ]
)

init_patch = [
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

init_insert = init_start + meta_index + 1

new_lines = list(lines)

new_lines[
    init_insert:init_insert
] = init_patch

source_after_init = "\n".join(new_lines) + "\n"

ast.parse(source_after_init)

print("INIT PATCH AST: PASS")

# ============================================================
# 8. RE-FIND process()
# ============================================================

tree2 = ast.parse(source_after_init)

core2 = [
    node for node in tree2.body
    if isinstance(node, ast.ClassDef)
    and node.name == "MinhMiniCore"
][0]

process2 = [
    node for node in core2.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "process"
][0]

lines2 = source_after_init.splitlines()

process_start = process2.lineno - 1
process_end = process2.end_lineno

process_lines = lines2[
    process_start:process_end
]

# ============================================================
# 9. FIND META ANALYZE
# ============================================================

meta_analyze = [
    i for i, line in enumerate(process_lines)
    if "# META_ORCHESTRATOR_P42_ANALYZE" in line
]

if len(meta_analyze) != 1:
    raise RuntimeError(
        "Cannot uniquely locate META analysis block"
    )

meta_analyze_index = meta_analyze[0]

# ============================================================
# 10. FIND needs_clarification
# ============================================================

needs = [
    i for i, line in enumerate(process_lines)
    if "needs_clarification = bool(" in line
    and i > meta_analyze_index
]

if len(needs) != 1:
    raise RuntimeError(
        "Cannot uniquely locate needs_clarification"
    )

needs_index = needs[0]

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

contract_patch = [
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

contract_insert = process_start + needs_index

new_lines[
    contract_insert:contract_insert
] = contract_patch

source_after_contract = "\n".join(new_lines) + "\n"

ast.parse(source_after_contract)

print("CONTRACT BUILD AST: PASS")

# ============================================================
# 12. RE-FIND process() AGAIN
# ============================================================

tree3 = ast.parse(source_after_contract)

core3 = [
    node for node in tree3.body
    if isinstance(node, ast.ClassDef)
    and node.name == "MinhMiniCore"
][0]

process3 = [
    node for node in core3.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "process"
][0]

lines3 = source_after_contract.splitlines()

process_start3 = process3.lineno - 1
process_end3 = process3.end_lineno

process_lines3 = lines3[
    process_start3:process_end3
]

# ============================================================
# 13. FIND needs_clarification AGAIN
# ============================================================

needs3 = [
    i for i, line in enumerate(process_lines3)
    if "needs_clarification = bool(" in line
]

if len(needs3) != 1:
    raise RuntimeError(
        "Final needs_clarification location not unique"
    )

needs_index3 = needs3[0]

needs_line3 = process_lines3[needs_index3]

gate_indent = (
    needs_line3[
        :len(needs_line3)
        - len(needs_line3.lstrip())
    ]
)

# ============================================================
# 14. ADD CONTRACT GATE AFTER EXISTING CLARIFICATION SETUP
# ============================================================

# Find the end of the existing bool(...) assignment.
depth = 0
end_index = None

for i in range(
    needs_index3,
    len(process_lines3),
):
    line = process_lines3[i]

    depth += line.count("(")
    depth -= line.count(")")

    if i > needs_index3 and depth <= 0:
        end_index = i
        break

if end_index is None:
    raise RuntimeError(
        "Cannot locate end of needs_clarification expression"
    )

gate_patch = [
    "",
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
    gate_indent + "if contract_blocks_execution:",
    gate_indent + "    needs_clarification = True",
]

absolute_gate_insert = (
    process_start3
    + end_index
    + 1
)

new_lines[
    absolute_gate_insert:absolute_gate_insert
] = gate_patch

final_source = "\n".join(new_lines) + "\n"

# ============================================================
# 15. FINAL AST
# ============================================================

ast.parse(final_source)

print("FINAL AST: PASS")

# ============================================================
# 16. REQUIRED MARKERS
# ============================================================

required_markers = [
    "# EXECUTION_CONTRACT_P44_INIT",
    "# EXECUTION_CONTRACT_P44_LAST_RESULT_INIT",
    "# EXECUTION_CONTRACT_P44_BUILD",
    "# EXECUTION_CONTRACT_P44_GATE",
    "self.execution_contract_builder",
    "self.last_execution_contract",
    "execution_contract = self.execution_contract_builder.build(",
    "if contract_blocks_execution:",
    "needs_clarification = True",
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
# 17. BACKUP CURRENT main.py
# ============================================================

shutil.copy2(
    MAIN,
    BACKUP,
)

if not BACKUP.exists():
    raise RuntimeError(
        "Backup creation failed"
    )

print("BACKUP: PASS")
print("BACKUP FILE:", BACKUP.name)

# ============================================================
# 18. WRITE main.py
# ============================================================

MAIN.write_text(
    final_source,
    encoding="utf-8",
)

print("PATCH STATUS: PASS")
print("MAIN.PY UPDATED")
print("BACKUP:", BACKUP.name)
