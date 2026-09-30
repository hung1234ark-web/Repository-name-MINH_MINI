from pathlib import Path
import ast
import shutil

MAIN = Path("main.py")
BACKUP = Path("main_p44_reasoning_context_final_before.py")

print("=== P4-4 REASONING CONTEXT FINAL PATCH ===")

if not MAIN.exists():
    raise SystemExit("ERROR: Không tìm thấy main.py")

source = MAIN.read_text(encoding="utf-8")

# ------------------------------------------------------------
# 1. AST CHECK
# ------------------------------------------------------------

try:
    tree = ast.parse(source)
except SyntaxError as exc:
    raise SystemExit(
        f"ERROR: main.py lỗi syntax: {exc}"
    )

print("ORIGINAL AST: PASS")

# ------------------------------------------------------------
# 2. CHECK PROCESS
# ------------------------------------------------------------

classes = [
    node
    for node in tree.body
    if isinstance(node, ast.ClassDef)
    and node.name == "MinhMiniCore"
]

if len(classes) != 1:
    raise SystemExit(
        "ERROR: Không xác định duy nhất MinhMiniCore."
    )

process_nodes = [
    node
    for node in classes[0].body
    if isinstance(node, ast.FunctionDef)
    and node.name == "process"
]

if len(process_nodes) != 1:
    raise SystemExit(
        "ERROR: Không xác định duy nhất MinhMiniCore.process()."
    )

print(
    "MinhMiniCore.process(): "
    f"{process_nodes[0].lineno}-"
    f"{process_nodes[0].end_lineno}"
)

# ------------------------------------------------------------
# 3. PREVENT DUPLICATE PATCH
# ------------------------------------------------------------

MARKER = "# P44_REASONING_CONTEXT_FINAL"

if MARKER in source:
    print("PATCH ALREADY EXISTS: PASS")
    raise SystemExit(0)

# ------------------------------------------------------------
# 4. SAVE ORIGINAL BRAIN DECISION
# ------------------------------------------------------------

old_brain = """        if decision is None:
            decision = fallback_decision(
                completed
            )

        # ----------------------------------------------------
        # 3. ROUTER GUARD
"""

new_brain = """        if decision is None:
            decision = fallback_decision(
                completed
            )

        # P44_REASONING_CONTEXT_FINAL
        # Giữ nguyên quyết định gốc của Brain cho THINK X,
        # Meta-Orchestrator và Execution Contract.
        reasoning_decision = decision

        # ----------------------------------------------------
        # 3. ROUTER GUARD
"""

if old_brain not in source:
    raise SystemExit(
        "ERROR: Không tìm thấy đúng đoạn Brain -> Router."
    )

source = source.replace(
    old_brain,
    new_brain,
    1,
)

print("REASONING DECISION SAVE: PASS")

# ------------------------------------------------------------
# 5. THINK X MUST USE ORIGINAL DECISION
# ------------------------------------------------------------

old_think = """                think_result = self.think_x.think(
                    completed,
                    decision,
                    current_goal,
                )"""

new_think = """                think_result = self.think_x.think(
                    completed,
                    reasoning_decision,
                    current_goal,
                )"""

if old_think not in source:
    raise SystemExit(
        "ERROR: Không tìm thấy THINK X integration."
    )

source = source.replace(
    old_think,
    new_think,
    1,
)

print("THINK X CONTEXT: PASS")

# ------------------------------------------------------------
# 6. META MUST USE ORIGINAL DECISION
# ------------------------------------------------------------

old_meta = """                meta_result = self.meta_orchestrator.orchestrate(
                    completed,
                    decision,
                    think_result,
                    current_goal,
                )"""

new_meta = """                meta_result = self.meta_orchestrator.orchestrate(
                    completed,
                    reasoning_decision,
                    think_result,
                    current_goal,
                )"""

if old_meta not in source:
    raise SystemExit(
        "ERROR: Không tìm thấy Meta-Orchestrator integration."
    )

source = source.replace(
    old_meta,
    new_meta,
    1,
)

print("META CONTEXT: PASS")

# ------------------------------------------------------------
# 7. REMOVE OLD P4-4 CONTEXT FIX
# ------------------------------------------------------------

start_marker = "                # EXECUTION_CONTRACT_P44_CONTEXT_FIX"
end_marker = """                execution_contract = self.execution_contract_builder.build(
                    completed,
                    contract_meta,
                )"""

start = source.find(start_marker)

if start == -1:
    raise SystemExit(
        "ERROR: Không tìm thấy P4-4 CONTEXT FIX cũ."
    )

end = source.find(end_marker, start)

if end == -1:
    raise SystemExit(
        "ERROR: Không tìm thấy điểm kết thúc CONTEXT FIX."
    )

# Giữ lại câu build contract, nhưng thay context cũ
replacement = """                contract_meta = meta_result

                execution_contract = self.execution_contract_builder.build(
                    completed,
                    contract_meta,
                )"""

source = (
    source[:start]
    + replacement
    + source[end + len(end_marker):]
)

print("OLD CONTEXT FIX REMOVED: PASS")

# ------------------------------------------------------------
# 8. CONTRACT GATE MUST USE ORIGINAL INTENT
# ------------------------------------------------------------

old_gate = """            contract_intent = get_decision_value(
                decision,
                'intent',
                '',
            )"""

new_gate = """            contract_intent = get_decision_value(
                reasoning_decision,
                'intent',
                '',
            )"""

if old_gate not in source:
    raise SystemExit(
        "ERROR: Không tìm thấy CONTRACT GATE."
    )

source = source.replace(
    old_gate,
    new_gate,
    1,
)

print("CONTRACT GATE CONTEXT: PASS")

# ------------------------------------------------------------
# 9. FINAL AST
# ------------------------------------------------------------

try:
    ast.parse(source)
except SyntaxError as exc:
    raise SystemExit(
        f"ERROR: Patch tạo syntax error: {exc}"
    )

print("FINAL AST: PASS")

# ------------------------------------------------------------
# 10. REQUIRED CHECKS
# ------------------------------------------------------------

checks = [
    (
        MARKER,
        "P44_REASONING_CONTEXT_FINAL",
    ),
    (
        "reasoning_decision = decision",
        "reasoning_decision",
    ),
    (
        "self.think_x.think(\n                    completed,\n                    reasoning_decision,",
        "THINK X uses reasoning_decision",
    ),
    (
        "self.meta_orchestrator.orchestrate(\n                    completed,\n                    reasoning_decision,",
        "META uses reasoning_decision",
    ),
    (
        "contract_meta = meta_result",
        "CONTRACT uses meta_result",
    ),
    (
        "get_decision_value(\n                reasoning_decision,\n                'intent',",
        "CONTRACT GATE uses reasoning_decision",
    ),
]

for needle, label in checks:
    if needle not in source:
        raise SystemExit(
            f"ERROR: CHECK FAILED: {label}"
        )

    print(
        f"CHECK: {label} = PASS"
    )

# ------------------------------------------------------------
# 11. BACKUP
# ------------------------------------------------------------

if BACKUP.exists():
    raise SystemExit(
        f"ERROR: Backup đã tồn tại: {BACKUP.name}"
    )

shutil.copy2(MAIN, BACKUP)

print("BACKUP: PASS")
print(f"BACKUP FILE: {BACKUP.name}")

# ------------------------------------------------------------
# 12. WRITE
# ------------------------------------------------------------

MAIN.write_text(
    source,
    encoding="utf-8",
)

print("PATCH STATUS: PASS")
print("MAIN.PY UPDATED")
