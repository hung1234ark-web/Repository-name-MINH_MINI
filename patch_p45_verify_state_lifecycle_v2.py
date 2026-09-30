from pathlib import Path
import ast
import shutil

MAIN = Path("main.py")
BACKUP = Path("main_p45_verify_state_lifecycle_before.py")

print("=== P4-5 VERIFY STATE LIFECYCLE PATCH V2 ===")

if not MAIN.exists():
    raise SystemExit("ERROR: main.py not found")

source = MAIN.read_text(encoding="utf-8")

print("ORIGINAL AST:", end=" ")
ast.parse(source)
print("PASS")

if "# P45_VERIFY_STATE_LIFECYCLE_V2" in source:
    raise SystemExit("PATCH ALREADY EXISTS: stop safely")

if BACKUP.exists():
    raise SystemExit(f"ERROR: backup already exists: {BACKUP}")

# ---------------------------------------------------------
# Locate the REAL MinhMiniCore.process()
# ---------------------------------------------------------

tree = ast.parse(source)

class_node = None
process_node = None

for node in tree.body:
    if isinstance(node, ast.ClassDef) and node.name == "MinhMiniCore":
        class_node = node
        break

if class_node is None:
    raise SystemExit("ERROR: class MinhMiniCore not found")

for node in class_node.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if node.name == "process":
            process_node = node
            break

if process_node is None:
    raise SystemExit("ERROR: MinhMiniCore.process() not found")

print(
    f"REAL PROCESS: FOUND "
    f"lines {process_node.lineno}-{process_node.end_lineno}"
)

# ---------------------------------------------------------
# Backup
# ---------------------------------------------------------

shutil.copy2(MAIN, BACKUP)

print("BACKUP: PASS")
print("BACKUP FILE:", BACKUP)

# ---------------------------------------------------------
# 1. Reset verification state at the beginning of the
#    REAL MinhMiniCore.process()
# ---------------------------------------------------------

anchor1 = """        self.turn_count += 1

        log(
            f"USER: {original}"
        )
"""

replacement1 = """        self.turn_count += 1

        # P45_VERIFY_STATE_LIFECYCLE_V2
        self.last_execution_verification = None

        log(
            f"USER: {original}"
        )
"""

if anchor1 not in source:
    raise SystemExit(
        "ERROR: real process() turn-start anchor not found"
    )

source = source.replace(anchor1, replacement1, 1)

print("TURN RESET: PASS")

# ---------------------------------------------------------
# 2. Explicitly mark clarification as blocked
# ---------------------------------------------------------

anchor2 = """        if needs_clarification:

            answer = self.make_clarification(
                completed,
                decision,
            )
"""

replacement2 = """        if needs_clarification:

            # P45_VERIFY_STATE_LIFECYCLE_V2
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
                "message": completed,
            }

            answer = self.make_clarification(
                completed,
                decision,
            )
"""

if anchor2 not in source:
    raise SystemExit(
        "ERROR: clarification anchor not found"
    )

source = source.replace(anchor2, replacement2, 1)

print("CLARIFICATION BLOCKED STATE: PASS")

# ---------------------------------------------------------
# Final AST validation
# ---------------------------------------------------------

print("FINAL AST:", end=" ")
ast.parse(source)
print("PASS")

MAIN.write_text(
    source,
    encoding="utf-8",
)

print("CHECK: real MinhMiniCore.process() = PASS")
print("CHECK: verification state reset = PASS")
print("CHECK: clarification blocked state = PASS")
print("CHECK: final AST = PASS")
print("PATCH STATUS: PASS")
print("MAIN.PY UPDATED")
