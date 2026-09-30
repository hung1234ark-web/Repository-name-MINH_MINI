from pathlib import Path
import ast
import shutil
import re

MAIN = Path("main.py")
BACKUP = Path("main_p44_reasoning_context_before.py")

if not MAIN.exists():
    raise SystemExit("ERROR: Không tìm thấy main.py")

source = MAIN.read_text(encoding="utf-8")

print("=== P4-4 REASONING CONTEXT PATCH ===")

# ------------------------------------------------------------
# 1. AST CHECK BEFORE
# ------------------------------------------------------------

try:
    tree = ast.parse(source)
except SyntaxError as exc:
    raise SystemExit(
        f"ERROR: main.py đang lỗi syntax: {exc}"
    )

print("ORIGINAL AST: PASS")

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

cls = classes[0]

process_nodes = [
    node
    for node in cls.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "process"
]

if len(process_nodes) != 1:
    raise SystemExit(
        "ERROR: Không xác định duy nhất MinhMiniCore.process()."
    )

process_node = process_nodes[0]

print(
    f"MinhMiniCore.process(): "
    f"{process_node.lineno}-{process_node.end_lineno}"
)

# ------------------------------------------------------------
# 2. EXISTING PATCH CHECK
# ------------------------------------------------------------

MARKER = "# P44_REASONING_CONTEXT_PATCH"

if MARKER in source:
    print("PATCH ALREADY EXISTS: PASS")
    raise SystemExit(0)

# ------------------------------------------------------------
# 3. FIND BRAIN -> ROUTING BLOCK
# ------------------------------------------------------------

brain_pattern = re.compile(
    r"""
    (?P<indent>^[ \t]*)
    decision\s*=\s*brain_think\(
        self\.brain,
        completed,
    \)
    """,
    re.MULTILINE | re.VERBOSE,
)

brain_match = brain_pattern.search(source)

if not brain_match:
    raise SystemExit(
        "ERROR: Không tìm thấy brain_think(self.brain, completed)."
    )

indent = brain_match.group("indent")

# ------------------------------------------------------------
# 4. INSERT IMMUTABLE REASONING DECISION
# ------------------------------------------------------------

reasoning_block = f'''{indent}{MARKER}
{indent}# Giữ decision gốc cho THINK X / META / CONTRACT.
{indent}# Main vẫn có thể route decision riêng để trả lời clarification.
{indent}reasoning_decision = decision

'''

source = (
    source[:brain_match.end()]
    + "\n"
    + reasoning_block
    + source[brain_match.end():]
)

# ------------------------------------------------------------
# 5. REPLACE THINK X INPUT
# ------------------------------------------------------------

old_think = """think_result = self.think_x.think(
                    completed,
                    decision,
                    current_goal,
                )"""

new_think = """think_result = self.think_x.think(
                    completed,
                    reasoning_decision,
                    current_goal,
                )"""

if old_think not in source:
    raise SystemExit(
        "ERROR: Không tìm thấy đoạn THINK X integration hiện tại."
    )

source = source.replace(
    old_think,
    new_think,
    1,
)

print("THINK X CONTEXT PATCH: PASS")

# ------------------------------------------------------------
# 6. REPLACE META INPUT
# ------------------------------------------------------------

old_meta = """meta_result = self.meta_orchestrator.orchestrate(
                    completed,
                    decision,
                    think_result,
                    current_goal,
                )"""

new_meta = """meta_result = self.meta_orchestrator.orchestrate(
                    completed,
                    reasoning_decision,
                    think_result,
                    current_goal,
                )"""

if old_meta not in source:
    raise SystemExit(
        "ERROR: Không tìm thấy đoạn Meta-Orchestrator integration hiện tại."
    )

source = source.replace(
    old_meta,
    new_meta,
    1,
)

print("META CONTEXT PATCH: PASS")

# ------------------------------------------------------------
# 7. FINAL AST CHECK
# ------------------------------------------------------------

try:
    ast.parse(source)
except SyntaxError as exc:
    raise SystemExit(
        f"ERROR: Patch tạo syntax error: {exc}"
    )

print("FINAL AST: PASS")

# ------------------------------------------------------------
# 8. VERIFY REQUIRED MARKERS
# ------------------------------------------------------------

checks = [
    (
        MARKER,
        "P44_REASONING_CONTEXT_PATCH",
    ),
    (
        "reasoning_decision = decision",
        "reasoning_decision assignment",
    ),
    (
        "completed,\n                    reasoning_decision,\n                    current_goal,",
        "THINK X / META reasoning context",
    ),
]

for needle, label in checks:
    if needle not in source:
        raise SystemExit(
            f"ERROR: CHECK FAILED: {label}"
        )
    print(f"CHECK: {label} = PASS")

# ------------------------------------------------------------
# 9. BACKUP
# ------------------------------------------------------------

if BACKUP.exists():
    raise SystemExit(
        f"ERROR: Backup đã tồn tại: {BACKUP.name}\n"
        "Không ghi đè backup cũ."
    )

shutil.copy2(MAIN, BACKUP)

print("BACKUP: PASS")
print(f"BACKUP FILE: {BACKUP.name}")

# ------------------------------------------------------------
# 10. WRITE
# ------------------------------------------------------------

MAIN.write_text(source, encoding="utf-8")

print("PATCH STATUS: PASS")
print("MAIN.PY UPDATED")
