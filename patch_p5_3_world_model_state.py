from pathlib import Path
import py_compile
import shutil

BASE = Path(__file__).resolve().parent
MAIN = BASE / "main.py"
BACKUP = BASE / "main.py.before_p5_3_world_model_state"

text = MAIN.read_text(encoding="utf-8")

if "P5_WORLD_MODEL_BLOCKED_OBSERVATION" in text:
    raise SystemExit(
        "ABORT: P5-3 blocked-state patch already exists."
    )

if not BACKUP.exists():
    shutil.copy2(MAIN, BACKUP)
    print(f"BACKUP CREATED: {BACKUP}")
else:
    print(f"BACKUP EXISTS: {BACKUP}")

needle = """            answer = self.make_clarification(
                completed,
                decision,
            )
"""

insert = """            # P5_WORLD_MODEL_BLOCKED_OBSERVATION
            # Clarification khong phai execution.
            # World Model phai nhan state hien tai,
            # khong duoc giu observation PASS cua turn truoc.
            if self.world_model is not None:
                try:
                    blocked_observation = {
                        "message": completed,
                        "intent": get_decision_value(
                            decision,
                            "intent",
                            "",
                        ),
                        "tool": get_decision_value(
                            decision,
                            "tool",
                            "",
                        ),
                        "action": get_decision_value(
                            decision,
                            "action",
                            "",
                        ),
                        "target": get_decision_value(
                            decision,
                            "target",
                            "",
                        ),
                        "answer_present": False,
                        "execution_success": None,
                        "verification": dict(
                            self.last_execution_verification
                        ),
                    }

                    self.world_model.record_observation(
                        blocked_observation
                    )

                    self.world_model.set_goal(
                        {
                            "text": completed,
                            "intent": get_decision_value(
                                decision,
                                "intent",
                                "",
                            ),
                            "action": get_decision_value(
                                decision,
                                "action",
                                "",
                            ),
                            "target": get_decision_value(
                                decision,
                                "target",
                                "",
                            ),
                            "status": "blocked",
                        }
                    )

                except Exception as exc:
                    log(
                        "WORLD MODEL BLOCKED STATE ERROR: "
                        + repr(exc)
                    )

"""

if needle not in text:
    raise SystemExit(
        "ABORT: clarification anchor not found."
    )

text = text.replace(
    needle,
    insert + needle,
    1,
)

MAIN.write_text(
    text,
    encoding="utf-8",
)

py_compile.compile(
    str(MAIN),
    doraise=True,
)

print("MAIN.PY WRITE     : PASS")
print("COMPILE           : PASS")

import main

instance = main.MINH

if getattr(instance, "world_model", None) is None:
    raise SystemExit(
        "FAIL: World Model unavailable."
    )

print("IMPORT            : PASS")
print("WORLD MODEL       : PASS")

print("=" * 64)
print("P5-3 STATE PATCH: PASS")
print("=" * 64)
print("P4-5 EXECUTION    : UNCHANGED")
print("P4-5 VERIFY       : UNCHANGED")
print("BRAIN             : UNCHANGED")
print("AUTO EXECUTION    : NO")
print("=" * 64)
