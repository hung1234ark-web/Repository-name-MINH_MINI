from pathlib import Path
import ast
import shutil

MAIN = Path("main.py")
BACKUP = Path("main_p45_verify_state_before.py")

print("=== P4-5 VERIFY STATE LIFECYCLE PATCH ===")

source = MAIN.read_text(encoding="utf-8")
ast.parse(source)

print("ORIGINAL AST: PASS")

if "# P45_VERIFY_STATE_LIFECYCLE" in source:
    raise RuntimeError(
        "P4-5 VERIFY STATE LIFECYCLE đã tồn tại. Không patch lần nữa."
    )

if "self.last_execution_verification = None" not in source:
    raise RuntimeError(
        "Không tìm thấy last_execution_verification foundation."
    )

if "if needs_clarification:" not in source:
    raise RuntimeError(
        "Không tìm thấy clarification gate."
    )

shutil.copy2(MAIN, BACKUP)

print("BACKUP: PASS")
print("BACKUP FILE:", BACKUP.name)

# ============================================================
# 1. RESET STATE AT START OF EACH PROCESS TURN
# ============================================================

anchor = """        self.turn_count += 1
        log("USER: " + original)
"""

if anchor not in source:
    raise RuntimeError(
        "Không tìm thấy process turn-start anchor."
    )

replacement = """        self.turn_count += 1

        # P45_VERIFY_STATE_LIFECYCLE
        # Mỗi lượt phải bắt đầu với execution verification sạch.
        self.last_execution_verification = None

        log("USER: " + original)
"""

source = source.replace(
    anchor,
    replacement,
    1,
)

print("TURN RESET: PASS")

# ============================================================
# 2. EXPLICIT BLOCKED STATE WHEN CLARIFICATION HAPPENS
# ============================================================

anchor = """        if needs_clarification:
            answer = self.make_clarification(completed, decision)
"""

if anchor not in source:
    raise RuntimeError(
        "Không tìm thấy clarification branch."
    )

replacement = """        if needs_clarification:

            # P45_VERIFY_STATE_LIFECYCLE
            # Clarification không phải execution.
            # Không được đánh dấu execution là PASS.
            self.last_execution_verification = {
                "verified": False,
                "status": "blocked",
                "success": None,
                "tool": get_decision_value(
                    decision,
                    "tool",
                    "",
                ),
                "intent": get_decision_value(
                    decision,
                    "intent",
                    "",
                ),
                "answer_present": False,
                "error": "",
                "checks": [
                    "execution_not_started",
                    "clarification_required",
                ],
            }

            answer = self.make_clarification(completed, decision)
"""

source = source.replace(
    anchor,
    replacement,
    1,
)

print("CLARIFICATION STATE: PASS")

# ============================================================
# 3. FINAL AST CHECK
# ============================================================

ast.parse(source)

print("FINAL AST: PASS")

# ============================================================
# WRITE
# ============================================================

MAIN.write_text(
    source,
    encoding="utf-8",
)

print("CHECK: P45_VERIFY_STATE_LIFECYCLE = PASS")
print("CHECK: turn reset = PASS")
print("CHECK: clarification blocked state = PASS")
print("PATCH STATUS: PASS")
print("MAIN.PY UPDATED")
