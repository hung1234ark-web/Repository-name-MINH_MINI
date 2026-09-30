from pathlib import Path
import shutil

BASE = Path(__file__).resolve().parent
MAIN = BASE / "main.py"
BACKUP = BASE / "main.py.before_debate_runtime_fix_v2"

if not MAIN.exists():
    raise RuntimeError(f"Khong tim thay {MAIN}")

source = MAIN.read_text(encoding="utf-8")

START = "    def process_debate(\n"
NEXT = "\n    # --------------------------------------------------------\n    # NORMALIZE\n"

start = source.find(START)

if start == -1:
    raise RuntimeError(
        "Khong tim thay process_debate() trong main.py"
    )

end = source.find(NEXT, start)

if end == -1:
    raise RuntimeError(
        "Khong tim thay diem ket thuc process_debate()."
    )

old_method = source[start:end]

if "DEBATE_1_1_GATE" not in source:
    raise RuntimeError(
        "Khong tim thay DEBATE gate. Dung patch de bao toan an toan."
    )

if "def verify_execution_result(" not in source:
    raise RuntimeError(
        "Khong tim thay P4-5 verifier."
    )

# Backup
if not BACKUP.exists():
    shutil.copy2(MAIN, BACKUP)

new_method = '''    def process_debate(
        self,
        message: str,
    ) -> str | None:
        """
        DEBATE runtime bridge.

        DEBATE chi phan tich ky thuat.
        Khong thuc thi Action.
        Khong thuc thi Web.
        Khong goi Execution Controller.
        Khong goi Execution Contract.
        Khong tu dong thay doi project.
        """

        if self.debate is None:
            return None

        try:
            detector = getattr(
                self.debate,
                "is_debate_command",
                None,
            )

            if not callable(detector):
                log(
                    "DEBATE ERROR: is_debate_command() unavailable"
                )
                return None

            if not detector(message):
                return None

            # ------------------------------------------------
            # DEBATE ANALYSIS
            # ------------------------------------------------

            analyzer = getattr(
                self.debate,
                "analyze",
                None,
            )

            if not callable(analyzer):
                log(
                    "DEBATE ERROR: analyze() unavailable"
                )
                return (
                    "DEBATE chua san sang."
                )

            result = analyzer(
                message
            )

            if result is None:
                return (
                    "Minh chua tao duoc phan tich "
                    "DEBATE cho yeu cau nay."
                )

            # ------------------------------------------------
            # DEBATE FORMAT
            # ------------------------------------------------

            formatter = getattr(
                self.debate,
                "format_result",
                None,
            )

            if callable(formatter):
                answer = formatter(
                    result
                )
            else:
                answer = str(
                    result
                )

            answer = clean_text(
                answer
            )

            if not answer:
                return (
                    "Minh chua tao duoc phan tich "
                    "DEBATE cho yeu cau nay."
                )

            # ------------------------------------------------
            # EXECUTION BLOCK
            # ------------------------------------------------
            # DEBATE tuyet doi khong thuc thi thay doi.
            return answer

        except Exception as exc:

            log(
                "DEBATE ERROR: "
                + traceback.format_exc()
            )

            return (
                "Minh gap loi khi phan tich /debate: "
                + clean_text(
                    str(exc)
                )
            )

'''

updated = (
    source[:start]
    + new_method
    + source[end:]
)

# ------------------------------------------------------------
# SAFETY CHECKS BEFORE WRITE
# ------------------------------------------------------------

checks = {
    "debate_init": "self.debate =" in updated,
    "debate_gate": "DEBATE_1_1_GATE" in updated,
    "debate_analyze": "self.debate.analyze" in updated,
    "debate_format": "self.debate.format_result" in updated,
    "p45_verifier": "def verify_execution_result(" in updated,
    "execution_controller": "ExecutionController" in updated,
    "execution_contract": "execution_contract" in updated,
    "no_debate_execution_handler": '"debate": handle_' not in updated,
    "no_old_debate_call": "self.debate.debate(" not in updated,
}

failed = [
    name
    for name, ok in checks.items()
    if not ok
]

if failed:
    raise RuntimeError(
        "SAFETY CHECK FAILED. "
        "main.py CHUA BI GHI.\n"
        + "\n".join(
            f"- {name}"
            for name in failed
        )
    )

if updated.count(
    "def process_debate("
) != 1:
    raise RuntimeError(
        "Khong dung 1 process_debate()."
    )

# ------------------------------------------------------------
# WRITE
# ------------------------------------------------------------

MAIN.write_text(
    updated,
    encoding="utf-8",
)

print()
print("=" * 60)
print("DEBATE RUNTIME FIX V2 COMPLETE")
print("=" * 60)
print(f"FILE              : {MAIN}")
print(f"BACKUP            : {BACKUP}")
print("ANALYZE            : PASS")
print("FORMAT_RESULT      : PASS")
print("OLD debate() CALL  : REMOVED")
print("DEBATE GATE        : PRESERVED")
print("P4-5               : PRESERVED")
print("EXECUTION HANDLER  : NOT ADDED")
print("=" * 60)
