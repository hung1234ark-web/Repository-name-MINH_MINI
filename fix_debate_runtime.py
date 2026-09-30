from pathlib import Path
import re
import shutil

BASE = Path(__file__).resolve().parent
MAIN = BASE / "main.py"
BACKUP = BASE / "main.py.before_debate_runtime_fix"

START_MARKER = "    def process_debate(self, message):"
NEXT_MARKER = "    def "

if not MAIN.exists():
    raise RuntimeError(f"Khong tim thay: {MAIN}")

source = MAIN.read_text(encoding="utf-8")

# ------------------------------------------------------------
# SAFETY
# ------------------------------------------------------------

if "DEBATE_1_1_GATE" not in source:
    raise RuntimeError("Khong tim thay DEBATE gate. Khong sua main.py.")

if "def process_debate(self, message):" not in source:
    raise RuntimeError("Khong tim thay process_debate(). Khong sua main.py.")

if BACKUP.exists():
    print(f"BACKUP DA TON TAI: {BACKUP}")
else:
    shutil.copy2(MAIN, BACKUP)
    print(f"BACKUP CREATED: {BACKUP}")

# ------------------------------------------------------------
# FIND process_debate()
# ------------------------------------------------------------

start = source.find(START_MARKER)

if start < 0:
    raise RuntimeError("Khong tim thay dau process_debate().")

# Find next class-level method after process_debate.
next_pos = source.find("\n    def ", start + len(START_MARKER))

if next_pos < 0:
    raise RuntimeError("Khong tim thay method tiep theo sau process_debate().")

old_method = source[start:next_pos]

# ------------------------------------------------------------
# NEW process_debate()
# ------------------------------------------------------------

new_method = '''    def process_debate(self, message):
        """
        DEBATE runtime bridge.

        IMPORTANT:
        - Chi phan tich.
        - Khong Action.
        - Khong Web.
        - Khong Execution Controller.
        - Khong Execution Contract.
        - Khong tu dong thay doi project.
        """
        if self.debate is None:
            return "DEBATE chua san sang."

        try:
            result = self.debate.analyze(message)
            return self.debate.format_result(result)

        except Exception as exc:
            return (
                "DEBATE gap loi khi phan tich. "
                f"Khong thuc thi thay doi nao. Loi: {exc}"
            )

'''

# ------------------------------------------------------------
# REPLACE ONLY process_debate()
# ------------------------------------------------------------

updated = source[:start] + new_method + source[next_pos:]

# ------------------------------------------------------------
# VERIFY BEFORE WRITE
# ------------------------------------------------------------

checks = {
    "debate_import": "debate_module = safe_import(" in updated,
    "debate_init": "self.debate = " in updated,
    "debate_method": "def process_debate(self, message):" in updated,
    "analyze_call": "result = self.debate.analyze(message)" in updated,
    "format_call": "return self.debate.format_result(result)" in updated,
    "debate_gate": "DEBATE_1_1_GATE" in updated,
    "p45_verify": "verify_execution_result" in updated,
    "execution_controller": "ExecutionController" in updated,
    "execution_contract": "execution_contract" in updated,
    "no_debate_handler": '"debate": handle_' not in updated,
}

failed = [name for name, ok in checks.items() if not ok]

if failed:
    raise RuntimeError(
        "SAFETY CHECK FAILED. Khong ghi main.py. "
        f"Failed: {', '.join(failed)}"
    )

# Ensure exactly one process_debate method.
if updated.count("def process_debate(self, message):") != 1:
    raise RuntimeError("So luong process_debate() khong hop le.")

# ------------------------------------------------------------
# WRITE
# ------------------------------------------------------------

MAIN.write_text(updated, encoding="utf-8")

print()
print("=" * 60)
print("DEBATE RUNTIME FIX COMPLETE")
print("=" * 60)
print(f"FILE              : {MAIN}")
print(f"BACKUP            : {BACKUP}")
print("PROCESS_DEBATE    : FIXED")
print("ANALYZE            : PASS")
print("FORMAT_RESULT      : PASS")
print("DEBATE GATE        : PRESERVED")
print("P4-5               : PRESERVED")
print("EXECUTION HANDLER  : NOT ADDED")
print("=" * 60)
